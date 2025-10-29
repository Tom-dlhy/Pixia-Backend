from fastapi import APIRouter, HTTPException, UploadFile, Form, File
from src.dto import ChatResponse
from src.config import database_settings, app_settings
from src.agents.root_agent import root_agent
from src.models import GenerativeToolOutput
from typing import List, Optional, Union
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.agents import LlmAgent
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
import asyncio

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
        # 🔍 Chercher la session existante (en mémoire OU en base de données)
        session = None
        current_session_service = None
        
        if session_id:
            # Essayer en mémoire D'ABORD
            session = await inmemory_service.get_session(
                app_name=settings.APP_NAME, user_id=user_id, session_id=session_id
            )
            
            if session:
                current_session_service = inmemory_service
                is_first_message = False
                logger.info(f"📍 Session trouvée en MÉMOIRE: {session_id}")
            else:
                # Fallback : chercher en base de données
                session = await db_session_service.get_session(
                    app_name=settings.APP_NAME, user_id=user_id, session_id=session_id
                )
                
                if session:
                    current_session_service = db_session_service
                    is_first_message = False
                    logger.info(f"📍 Session trouvée en BASE DE DONNÉES: {session_id}")
                else:
                    # Session n'existe nulle part
                    logger.warning(f"⚠️ Session {session_id} introuvable (mémoire et BD)")
                    # Créer une nouvelle session en BD pour cette session_id
                    session = await db_session_service.create_session(
                        app_name=settings.APP_NAME, 
                        user_id=user_id,
                        session_id=session_id
                    )
                    current_session_service = db_session_service
                    is_first_message = True
                    logger.info(f"✅ Nouvelle session créée en BD avec id: {session_id}")

        else:
            # Pas de session_id fournie, créer une nouvelle en BD
            session = await db_session_service.create_session(
                app_name=settings.APP_NAME, user_id=user_id
            )
            session_id = session.id
            current_session_service = db_session_service
            is_first_message = True
            logger.info(f"✅ Nouvelle session créée en BD: {session_id}")
            
        print(f"🆔 session_id: {session_id} | service: {type(current_session_service).__name__} | first_msg: {is_first_message}")
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

        # 🔄 BOUCLE DE RETRY - Max 3 tentatives pour gérer les sessions corrompues
        max_retries = 3
        retry_count = 0
        execution_session_id = session_id
        last_error = None

        while retry_count < max_retries:
            try:
                retry_count += 1
                logger.info(
                    f"🔄 [ATTEMPT {retry_count}/{max_retries}] "
                    f"Exécution du runner avec session_id={execution_session_id}"
                )

                runner = Runner(
                    agent=root_agent,
                    app_name=settings.APP_NAME,
                    session_service=current_session_service,
                    artifact_service=artifact_service,
                )
            

                # Flag pour vérifier si on a au moins une réponse valide
                received_valid_event = False
                null_event_count = 0

                async for event in runner.run_async(
                    user_id=user_id, session_id=execution_session_id, new_message=typed_message
                ):
                    # 🔍 Détection d'événements corrompus
                    if event.content is None:
                        null_event_count += 1
                        logger.warning(
                            f"⚠️ [EVENT-NULL #{null_event_count}] Événement reçu avec content=None | "
                            f"type={type(event).__name__}"
                        )
                        # Si trop d'événements NULL d'affilée, c'est suspect
                        if null_event_count > 2:
                            logger.error(
                                f"❌ Trop d'événements NULL ({null_event_count}), "
                                f"session probablement corrompue"
                            )
                            raise RuntimeError(
                                f"Session corrompue: {null_event_count} événements NULL consécutifs"
                            )
                        continue

                    # ✅ Au moins un événement valide reçu
                    received_valid_event = True
                    null_event_count = 0  # Réinitialiser le compteur
                    logger.debug(
                        f"📩 Event reçu: type={type(event).__name__} | has_content={event.content is not None}"
                    )
                    print(f"Event reçu: {event}")

                    # 🔧 Extraction des réponses de tools
                    if hasattr(event, "get_function_responses"):
                        func_responses = event.get_function_responses()
                        if func_responses:
                            for fr in func_responses:
                                tool_name = fr.name
                                tool_resp = fr.response
                                if tool_name and tool_resp:
                                    tool_result = tool_resp.get("result")
                                    logger.info(
                                        f"🛠️  Tool exécuté: {tool_name} | "
                                        f"result_type={type(tool_result).__name__}"
                                    )

                                    if tool_name in (
                                        "generate_exercises",
                                        "generate_courses",
                                        "generate_new_chapter",
                                        "generate_deepcourse",
                                    ):
                                        if isinstance(tool_result, GenerativeToolOutput):
                                            agent = tool_result.agent
                                            redirect_id = tool_result.redirect_id
                                            logger.info(
                                                f"✅ Générateur complété: agent={agent}, "
                                                f"redirect_id={redirect_id}"
                                            )

                    # ✅ Détection de réponse finale
                    if event.is_final_response():
                        logger.info("🎯 Événement final détecté")
                        if event.content and event.content.parts:
                            txt_reponse = event.content.parts[0].text
                            agent = event.author
                            
                        else:
                            logger.warning("⚠️ Événement final mais pas de contenu textuel")
                        break

                # ✅ Exécution réussie, sortir de la boucle de retry
                if received_valid_event:
                    logger.info(f"✅ [ATTEMPT {retry_count}] Succès - Au moins un événement valide reçu")
                    break
                else:
                    raise RuntimeError("Aucun événement valide reçu du runner")

            except (asyncio.TimeoutError, RuntimeError) as e:
                last_error = e
                logger.error(
                    f"❌ [ATTEMPT {retry_count}/{max_retries}] Erreur détectée: {type(e).__name__}: {e}"
                )

                # Si ce n'est pas la dernière tentative, supprimer l'ancienne session corrompue et réessayer
                if retry_count < max_retries:
                    logger.info(f"🔁 Suppression session corrompue et retry...")
                    try:
                        # Récupérer la session courante (potentiellement corrompue) du MÊME service
                        old_session = await current_session_service.get_session(
                            app_name=settings.APP_NAME,
                            user_id=user_id,
                            session_id=execution_session_id
                        )
                        
                        # Extraire les events valides
                        valid_events = []
                        if old_session:
                            if hasattr(old_session, 'events') and old_session.events:
                                # Filtrer les events: garder seulement ceux avec du contenu
                                valid_events = [e for e in old_session.events if e.content is not None]
                                logger.info(
                                    f"📋 {len(valid_events)}/{len(old_session.events)} events valides récupérés "
                                    f"(filtré {len(old_session.events) - len(valid_events)} events NULL)"
                                )
                            else:
                                logger.warning(f"⚠️ Aucun attribut 'events' ou vide")
                        else:
                            logger.error(f"❌ Ancienne session non trouvée")

                        # 🔒 CRITICAL: Étapes pour dupliquer les events
                        # 1. Récupérer les events valides (déjà fait plus haut)
                        # 2. Supprimer l'ancienne session (CASCADE supprime ses events)
                        # 3. Créer nouvelle session
                        # 4. Re-insérer les events valides → pas de conflit car anciens IDs libérés
                        
                        await current_session_service.delete_session(
                            app_name=settings.APP_NAME,
                            user_id=user_id,
                            session_id=execution_session_id
                        )
                        logger.info(f"🗑️  Session corrompue supprimée: {execution_session_id}")
                        logger.info(f"   → Les {len(valid_events)} events supprimés aussi (CASCADE)")

                        # Créer une NOUVELLE session propre
                        new_session = await current_session_service.create_session(
                            app_name=settings.APP_NAME, user_id=user_id
                        )
                        new_session_id = new_session.id
                        logger.info(f"✅ Nouvelle session créée: {new_session_id}")
                        
                        # 🔄 RE-INSÉRER les events valides dans la nouvelle session
                        # Maintenant qu'ancienne session est supprimée, les IDs d'events sont libres
                        if valid_events:
                            for event in valid_events:
                                await current_session_service.append_event(
                                    session=new_session,
                                    event=event
                                )
                            logger.info(f"✅ {len(valid_events)} events dupliqués dans nouvelle session")
                        else:
                            logger.warning(f"⚠️ Aucun event valide à dupliquer")
                        
                        # Utiliser la nouvelle session pour le retry
                        execution_session_id = new_session_id
                        logger.info(f"🔄 Switch vers nouvelle session avec events restaurés: {execution_session_id}")

                        # Attendre avant retry (backoff exponentiel)
                        wait_time = 2 ** (retry_count - 1)
                        logger.info(f"⏳ Attente de {wait_time}s avant retry...")
                        await asyncio.sleep(wait_time)
                        
                    except Exception as session_err:
                        logger.error(f"❌ Erreur lors du nettoyage/création de session: {session_err}")
                        logger.debug(f"   Traceback: ", exc_info=True)
                        raise
                else:
                    logger.error(f"❌ Échec après {max_retries} tentatives")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erreur agent persistante après {max_retries} tentatives: {str(last_error)}",
                    )

    except Exception as e:
        logger.exception("❌ Erreur pendant l'exécution du runner ADK")
        raise HTTPException(status_code=500, detail=f"Erreur agent : {e}")

    if not txt_reponse and (agent is not None and redirect_id is not None):
        txt_reponse = "Votre document a été généré avec succès."
    elif not txt_reponse:
        txt_reponse = " "

    end_time = time.monotonic()
    duration = end_time - start_time
    print(f"Durée totale: {duration:.2f} secondes")

    logger.info(f"agent={agent}")
    logger.info(f"redirect_id={redirect_id}")
    output = ChatResponse(
        session_id=session_id,
        answer=txt_reponse,
        agent=agent,
        redirect_id=redirect_id,
    )

    return output
