from fastapi import APIRouter, Depends, HTTPException
from src.dto import ChatResponse, ChatRequest, build_chat_response
from src.config import database_settings
from google.adk.sessions import Session
from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

session_service = DatabaseSessionService(
    db_url=database_settings.dsn, 
)

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Traite un message utilisateur via une session ADK."""

    user_id = req.user_id
    message = req.message
    files = req.files or []
    session_id = req.chat_id or f"session_{user_id}" 

    try:
        session = await session_service.load_session(session_id)
        if session is None:
            logger.info(f"🆕 Nouvelle session créée : {session_id}")
            session = Session.create(session_id, user_id=user_id)
    except Exception as e:
        logger.exception("❌ Erreur lors du chargement de la session")
        raise HTTPException(status_code=500, detail=f"Erreur de session : {e}")

    try:
        runner = Runner(session=session)
        result = await runner.run_async(message, files=files)
    except Exception as e:
        logger.exception("❌ Erreur pendant l'exécution du runner ADK")
        raise HTTPException(status_code=500, detail=f"Erreur agent : {e}")

    raw_answer = getattr(result, "content", None)
    agent_used = getattr(result, "agent", "default")

    if raw_answer is None:
        raise HTTPException(status_code=500, detail="Aucune réponse de l’agent.")

    response = build_chat_response(
        chat_id=session_id,
        agent_used=agent_used,
        raw_answer=raw_answer,
    )

    try:
        await session_service.save_session(session)
        logger.info(f"💾 Session {session_id} sauvegardée avec succès.")
    except Exception as e:
        logger.warning(f"⚠️ Échec de la sauvegarde de la session {session_id}: {e}")

    return response
