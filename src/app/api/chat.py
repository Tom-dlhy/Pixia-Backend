from fastapi import APIRouter, HTTPException, UploadFile, Form, File
from src.dto import ChatResponse
from src.config import database_settings, app_settings
from src.agents.root_agent import root_agent
from src.models import GenerativeToolOutput
from typing import List, Optional, Union
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types
from google.genai.types import Part
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from src.utils import set_request_context, final_context_builder
import json

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
    message_context: Optional[str] = Form(None),
):
    """Traite un message utilisateur via une session ADK."""
    start_time = time.monotonic()

    print(f"SESSION ID: {session_id}")

    set_request_context(
        document_id=document_id,
        session_id=session_id,
        user_id=user_id,
        deep_course_id=deep_course_id,
    )

    txt_reponse: Optional[str] = None
    agent = None
    redirect_id = None
    current_session_service = None
    is_first_message = False

    try:
        if session_id:
            session = await inmemory_service.get_session(
                app_name=settings.APP_NAME, user_id=user_id, session_id=session_id
            )

            if session:
                session_id = session.id
                current_session_service = inmemory_service
                is_first_message = False  
            else:
                session = await db_session_service.get_session(
                    app_name=settings.APP_NAME, user_id=user_id, session_id=session_id
                )
                current_session_service = db_session_service
                is_first_message = False  

        elif not session_id:
            session = await inmemory_service.create_session(
                app_name=settings.APP_NAME, user_id=user_id
            )
            session_id = session.id
            current_session_service = inmemory_service
            is_first_message = True 

    except Exception as e:
        logger.exception("❌ Erreur pendant la gestion de la session")
        raise HTTPException(status_code=500, detail=f"Erreur de session : {e}")

    if files:
        logger.info(f"📎 {len(files)} fichier(s) reçu(s)")
        for idx, upload_file in enumerate(files):
            try:

                file_bytes = await upload_file.read()
                file_mime_type = upload_file.content_type or "application/octet-stream"
                filename = upload_file.filename or f"file_{idx}"

                artifact_part = types.Part.from_bytes(
                    data=file_bytes, mime_type=file_mime_type
                )

                version = await artifact_service.save_artifact(
                    app_name=settings.APP_NAME,
                    user_id=user_id,
                    session_id=session_id,
                    filename=filename,
                    artifact=artifact_part,
                )

            except Exception as e:
                logger.error(
                    f"❌ Erreur lors de la sauvegarde du fichier {filename}: {e}"
                )


    try:
        if current_session_service is None:
            return ChatResponse(
                session_id=session_id,
                answer="Une erreur est survenue lors de la gestion de la session.",
                agent=agent,
                redirect_id=redirect_id,
            )

        if is_first_message:
            try:
                message_context = await final_context_builder(
                    message_context=message_context
                )
                message = message_context + message
            except Exception as e:
                logger.warning(f"⚠️ Erreur lors de l'enrichissement du contexte: {e}")

        parts = [Part(text=message)]

        try:
            artifact_keys = await artifact_service.list_artifact_keys(
                app_name=settings.APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )

            if artifact_keys:
                logger.info(
                    f"📂 Chargement de {len(artifact_keys)} artifact(s) pour le contexte"
                )
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

        try:
            for fid in get_gemini_files(session_id):  # type: ignore[arg-type]
                parts.append(Part.from_uri(file_uri=fid, mime_type="application/pdf"))
        except Exception:
            pass

        typed_message = types.Content(role="user", parts=parts)
        runner = Runner(
            agent=root_agent,
            app_name=settings.APP_NAME,
            session_service=current_session_service,
            artifact_service=artifact_service,
        )

        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=typed_message
        ):

            if hasattr(event, "get_function_responses"):
                func_responses = event.get_function_responses()
                if func_responses:
                    for fr in func_responses:
                        tool_name = fr.name
                        tool_resp = fr.response
                        if tool_name and tool_resp:
                            tool_result = tool_resp.get("result")

                            if tool_name in (
                                "generate_exercises",
                                "generate_courses",
                                "generate_new_chapter",
                                "generate_deepcourse",
                            ):
                                if isinstance(tool_result, GenerativeToolOutput):
                                    agent = tool_result.agent
                                    redirect_id = tool_result.redirect_id

            if event.is_final_response():
                if event.content and event.content.parts:
                    txt_reponse = event.content.parts[0].text
                break

    except Exception as e:
        logger.exception("❌ Erreur pendant l'exécution du runner ADK")
        raise HTTPException(status_code=500, detail=f"Erreur agent : {e}")

    if not txt_reponse and (agent is None and redirect_id is None):
        txt_reponse = "Votre document a été généré avec succès."
    elif not txt_reponse:
        txt_reponse = " "

    end_time = time.monotonic()
    duration = end_time - start_time
    print(f"Durée totale: {duration:.2f} secondes")

    logger.info(f"agent={agent}")
    output = ChatResponse(
        session_id=session_id,
        answer=txt_reponse,
        agent=agent,
        redirect_id=redirect_id,
    )

    return output
