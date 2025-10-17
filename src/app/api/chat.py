from fastapi import APIRouter, Depends, HTTPException, UploadFile
from src.dto import ChatResponse, ChatRequest, build_chat_response
from src.config import database_settings, app_settings
from src.agents.root_agent import root_agent
from src.models import ExerciseOutput, _validate_exercise_output

from typing import List, Optional, Union
from google.adk.sessions import Session
from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types
from google.genai.types import Part
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = app_settings


session_service = DatabaseSessionService(
    db_url=database_settings.dsn, 
)

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Traite un message utilisateur via une session ADK."""

    user_id: str = req.user_id
    message: str = req.message
    session_id: Optional[str] = req.session_id  # None si nouvelle conversation
    files = req.files or []  # support fichiers futur

    final_response: Optional[Union[str, dict, list]] = None
    author: Optional[str] = None

    # === Étape 1 : création ou récupération de session ===
    try:
        if not session_id:
            logger.info(f"🆕 Création d'une nouvelle session pour l'utilisateur {user_id}")
            session = await session_service.create_session(
                app_name=settings.APP_NAME,
                user_id=user_id
            )
            session_id = session.id
        else:
            logger.info(f"🔄 Chargement de la session existante {session_id} pour {user_id}")
            session = await session_service.get_session(
                app_name=settings.APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            if session is None:
                logger.warning(f"⚠️ Session {session_id} introuvable. Création d'une nouvelle.")
                session = await session_service.create_session(
                    app_name=settings.APP_NAME,
                    user_id=user_id
                )
                session_id = session.id

        logger.info(f"✅ Session opérationnelle : {session_id}")

    except Exception as e:
        logger.exception("❌ Erreur pendant la gestion de la session")
        raise HTTPException(status_code=500, detail=f"Erreur de session : {e}")

    # === Étape 2 : exécution du runner ADK ===
    try:
        typed_message = types.Content(role="user", parts=[Part(text=message)])
        runner = Runner(
            agent=root_agent,
            app_name=settings.APP_NAME,
            session_service=session_service
        )

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=typed_message
        ):

            # --- Réponse finale ---
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text

                    logger.info(f"✅ Réponse finale reçue pour la session {session_id}")
                    author = event.author
                break

            # --- Sortie d’un outil (tool output) ---
            elif hasattr(event, "get_function_responses"):
                func_responses = event.get_function_responses()
                if func_responses:
                    for fr in func_responses:
                        tool_name = fr.name
                        tool_resp = fr.response

                        if tool_name == "generate_exercises":
                            logging.info("✅ Tool 'generate_exercises' détecté")
                            if _validate_exercise_output(tool_resp):
                                final_response = _validate_exercise_output(tool_resp)
                                logger.info(f"✅ ExerciseOutput validé pour la session {session_id}")

    except Exception as e:
        logger.exception("❌ Erreur pendant l'exécution du runner ADK")
        raise HTTPException(status_code=500, detail=f"Erreur agent : {e}")

    # === Étape 3 : validation finale ===
    if not final_response:
        logger.error(f"Aucune réponse reçue pour la session {session_id}")
        raise HTTPException(status_code=500, detail="Aucune réponse de l’agent.")

    # === Étape 4 : construction de la réponse ===
    return build_chat_response(
        chat_id=session_id,  # TODO : renommer chat_id → session_id dans le DTO
        agent_used=author or "root_agent",  # Fallback si l’auteur n’est pas défini
        raw_answer=final_response
    )