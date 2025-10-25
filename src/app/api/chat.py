from fastapi import APIRouter, HTTPException, UploadFile, Form, File
from src.dto import ChatResponse
from src.config import database_settings, app_settings
from src.agents.root_agent import root_agent
from src.models import (
    _validate_exercise_output,
    _validate_course_output,
    _validate_chapter_output,
    _validate_deepcourse_output,
)
from src.bdd import DBManager
from src.models import ExerciseOutput, CourseOutput, DeepCourseOutput, Chapter
from src.utils import generate_new_chapter
from src.tools.deepcourse_tools import NewChapterRequest

from typing import List, Optional, Union, Dict
from uuid import uuid4
from google.adk.sessions import Session, InMemorySessionService
from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types
from google.genai.types import Part
import logging
import time 

from dotenv import load_dotenv
from src.utils import get_gemini_files

from google.adk.artifacts import InMemoryArtifactService
from src.tools.copilote_tools import set_document_id_context

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = app_settings


db_session_service = DatabaseSessionService(
    db_url=database_settings.dsn,
)

artifact_service = InMemoryArtifactService()

inmemory_service = InMemorySessionService()

current_session_service: Union[InMemorySessionService, DatabaseSessionService, None]


@router.post("", response_model=ChatResponse)
async def chat(
    user_id: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    deep_course_id: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
):
    """Traite un message utilisateur via une session ADK."""
    start_time = time.monotonic()

    final_response: Optional[
        Union[str, dict, list, ExerciseOutput, CourseOutput, DeepCourseOutput, Chapter]
    ] = None
    txt_reponse: Optional[str] = None
    agent = None
    redirect_id = None
    bdd_manager = DBManager()
    current_session_service = None

    # === Étape 1 : création ou récupération de session ===
    try:
        if session_id:
            session = await inmemory_service.get_session(
                app_name=settings.APP_NAME, user_id=user_id, session_id=session_id
            )

            if session:
                session_id = session.id
                current_session_service = inmemory_service
            else:
                session = await db_session_service.get_session(
                    app_name=settings.APP_NAME, user_id=user_id, session_id=session_id
                )
                current_session_service = db_session_service
                
                # Si session DB (copilote) et document_id fourni, le stocker dans le contexte
                if session and document_id:
                    set_document_id_context(document_id)
                    logger.info(f"📋 Context configuré avec document_id={document_id}")

        elif not session_id:
            session = await inmemory_service.create_session(
                app_name=settings.APP_NAME, user_id=user_id
            )
            session_id = session.id
            current_session_service = inmemory_service

    except Exception as e:
        logger.exception("❌ Erreur pendant la gestion de la session")
        raise HTTPException(status_code=500, detail=f"Erreur de session : {e}")

    # === Étape 1.5 : Sauvegarder les files dans artifact_service ===
    if files:
        logger.info(f"📎 {len(files)} fichier(s) reçu(s)")
        for idx, upload_file in enumerate(files):
            try:
                # Lire le contenu du fichier
                file_bytes = await upload_file.read()
                file_mime_type = upload_file.content_type or "application/octet-stream"
                filename = upload_file.filename or f"file_{idx}"
                
                logger.info(f"📄 Sauvegarde de {filename} ({file_mime_type}, {len(file_bytes)} bytes)")
                
                # Créer un Part artifact avec les bytes
                artifact_part = types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=file_mime_type
                )
                
                # Sauvegarder dans artifact_service
                version = await artifact_service.save_artifact(
                    app_name=settings.APP_NAME,
                    user_id=user_id,
                    session_id=session_id,
                    filename=filename,
                    artifact=artifact_part,
                )
                
                logger.info(f"✅ Artifact sauvegardé: {filename} (version {version})")
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de la sauvegarde du fichier {filename}: {e}")
                # Continue avec les autres fichiers même en cas d'erreur

    # === Étape 2 : exécution du runner ADK ===
    try:
        # Attach session files (PDFs uploaded to Gemini) to the user message
        parts = [Part(text=message)]
        
        # Ajouter les artifacts (fichiers uploadés) au message
        try:
            artifact_keys = await artifact_service.list_artifact_keys(
                app_name=settings.APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
            
            if artifact_keys:
                logger.info(f"📂 Chargement de {len(artifact_keys)} artifact(s) pour le contexte")
                for artifact_key in artifact_keys:
                    artifact_part = await artifact_service.load_artifact(
                        app_name=settings.APP_NAME,
                        user_id=user_id,
                        session_id=session_id,
                        filename=artifact_key,
                    )
                    if artifact_part:
                        parts.append(artifact_part)
                        logger.info(f"✅ Artifact ajouté au contexte: {artifact_key}")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors du chargement des artifacts: {e}")
        
        # Ajouter aussi les anciens fichiers Gemini (si ils existent)
        try:
            for fid in get_gemini_files(session_id):  # type: ignore[arg-type]
                parts.append(Part.from_uri(file_uri=fid, mime_type="application/pdf"))
        except Exception:
            # Non-fatal: continue without file parts if any issue arises
            pass

        typed_message = types.Content(role="user", parts=parts)

        if current_session_service is None:
            return ChatResponse(
                session_id=session_id,
                answer="Une erreur est survenue lors de la gestion de la session.",
                agent=agent,
                redirect_id=redirect_id,
            )

        runner = Runner(
            agent=root_agent,
            app_name=settings.APP_NAME,
            session_service=current_session_service,
            artifact_service=artifact_service,
        )

        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=typed_message
        ):

            # --- Réponse finale ---
            if event.is_final_response():
                if event.content and event.content.parts:
                    txt_reponse = event.content.parts[0].text
                break

            # --- Sortie d’un outil (tool output) ---
            elif hasattr(event, "get_function_responses"):
                func_responses = event.get_function_responses()
                if func_responses:
                    for fr in func_responses:
                        tool_name = fr.name
                        tool_resp = fr.response
                        if tool_name and tool_resp:
                            if tool_name == "generate_exercises":
                                if _validate_exercise_output(tool_resp):
                                    copilote_session_id = str(uuid4())
                                    await db_session_service.create_session(
                                        session_id=copilote_session_id,
                                        app_name=settings.APP_NAME,
                                        user_id=user_id,
                                    )
                                    final_response = _validate_exercise_output(
                                        tool_resp
                                    )
                                    if isinstance(final_response, ExerciseOutput):
                                        await bdd_manager.store_basic_document(
                                            content=final_response,
                                            session_id=copilote_session_id,
                                            sub=user_id,
                                        )
                                        agent = "exercise"
                                        redirect_id = copilote_session_id

                            elif tool_name == "generate_courses":
                                if _validate_course_output(tool_resp):
                                    copilote_session_id = str(uuid4())
                                    await db_session_service.create_session(
                                        session_id=copilote_session_id,
                                        app_name=settings.APP_NAME,
                                        user_id=user_id,
                                    )
                                    final_response = _validate_course_output(tool_resp)
                                    if isinstance(final_response, CourseOutput):
                                        await bdd_manager.store_basic_document(
                                            content=final_response,
                                            session_id=copilote_session_id,
                                            sub=user_id,
                                        )
                                        agent = "course"
                                        redirect_id = copilote_session_id

                            elif tool_name == "modify_course":
                                if _validate_course_output(tool_resp):
                                    final_response = _validate_course_output(tool_resp)
                                    if isinstance(final_response, CourseOutput):
                                        await bdd_manager.update_document(
                                            document_id=session_id,
                                            new_content=final_response,
                                        )

                            elif tool_name == "delete_course":
                                await bdd_manager.delete_document(
                                    document_id=session_id
                                )

                            elif tool_name == "generate_deepcourse":
                                validated = _validate_deepcourse_output(tool_resp)
                                if validated:
                                    final_response = validated
                                    if isinstance(final_response, DeepCourseOutput):

                                        try:
                                            # Créer les sessions et mapper les IDs pour chaque chapitre
                                            dict_session: List[Dict[str, str]] = []

                                            for chapter in final_response.chapters:
                                                try:
                                                    session_exercise = await db_session_service.create_session(
                                                        app_name=settings.APP_NAME,
                                                        user_id=user_id,
                                                    )
                                                    session_course = await db_session_service.create_session(
                                                        app_name=settings.APP_NAME,
                                                        user_id=user_id,
                                                    )
                                                    session_evaluation = await db_session_service.create_session(
                                                        app_name=settings.APP_NAME,
                                                        user_id=user_id,
                                                    )

                                                    chapter_sessions = {
                                                        "id_chapter": chapter.id_chapter,
                                                        "session_id_exercise": session_exercise.id,
                                                        "session_id_course": session_course.id,
                                                        "session_id_evaluation": session_evaluation.id,
                                                    }
                                                    dict_session.append(
                                                        chapter_sessions
                                                    )
                                                except Exception as e:
                                                    logger.error(
                                                        f"❌ Erreur lors de la création des sessions pour le chapitre {chapter.id_chapter}: {e}"
                                                    )
                                                    raise

                                            await bdd_manager.store_deepcourse(
                                                user_id=user_id,
                                                content=final_response,
                                                dict_session=dict_session,
                                            )
                                            agent = "deep-course"
                                            redirect_id = final_response.id
                                        except Exception as e:
                                            logger.error(
                                                f"❌ Erreur lors du stockage du deepcourse: {e}"
                                            )
                                            raise

                            elif tool_name == "call_generate_new_chapter":
                                if isinstance(tool_resp, NewChapterRequest):
                                    description_user = tool_resp.description_user
                                elif isinstance(tool_resp, dict):
                                    description_user = tool_resp.get("description_user", "")
                                else:
                                    description_user = ""
                                logger.info("✅ Tool 'call_generate_new_chapter' détecté")
                                if isinstance(deep_course_id, str):
                                    chapter = await generate_new_chapter(deepcourse_id=deep_course_id, description_user=description_user)

                                    validated = _validate_chapter_output(chapter)
                                    if validated:
                                        final_response = validated
                                        if isinstance(final_response, Chapter):
                                            logger.info(
                                                f"✅ Chapter validé pour la session {session_id}"
                                            )
                                            try:
                                                session_exercise = (
                                                    await db_session_service.create_session(
                                                        app_name=settings.APP_NAME,
                                                        user_id=user_id,
                                                    )
                                                )
                                                session_course = (
                                                    await db_session_service.create_session(
                                                        app_name=settings.APP_NAME,
                                                        user_id=user_id,
                                                    )
                                                )
                                                session_evaluation = (
                                                    await db_session_service.create_session(
                                                        app_name=settings.APP_NAME,
                                                        user_id=user_id,
                                                    )
                                                )
                                                await bdd_manager.store_chapter(
                                                    title=final_response.title,
                                                    user_id=user_id,
                                                    deepcourse_id=deep_course_id,
                                                    chapter_id=final_response.id_chapter,
                                                    session_exercise=session_exercise.id,
                                                    session_course=session_course.id,
                                                    session_evaluation=session_evaluation.id,
                                                    exercice=final_response.exercice,
                                                    course=final_response.course,
                                                    evaluation=final_response.evaluation,
                                                )
                                                agent = "deep-course"
                                                redirect_id = final_response.id_chapter
                                                logger.info(
                                                    f"✅ Chapter stocké avec succès : {final_response.id_chapter}"
                                                )
                                            except Exception as e:
                                                logger.error(
                                                    f"❌ Erreur lors du stockage du chapitre: {e}"
                                                )
                                                raise
                                        else:
                                            logger.warning(
                                                f"⚠️ Chapter validé mais pas une instance de Chapter"
                                            )
                                    else:
                                        logger.warning(
                                            f"⚠️ Impossible de valider le Chapter"
                                        )
                                else:
                                    logger.warning(
                                        f"⚠️ deep_course_id non fourni ou invalide"
                                    )                            

    except Exception as e:
        logger.exception("❌ Erreur pendant l'exécution du runner ADK")
        raise HTTPException(status_code=500, detail=f"Erreur agent : {e}")

    if not txt_reponse:
        txt_reponse = ""

    print("--- Chat API Timing ---")
    end_time = time.monotonic()
    duration = end_time - start_time
    print(f"Durée totale: {duration:.2f} secondes")

    output = ChatResponse(
        session_id=session_id,
        answer=txt_reponse,
        agent=agent,
        redirect_id=redirect_id,
    )

    return output


# =========================================================
# FIN DE LA ROUTE
# =========================================================
