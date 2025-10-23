from fastapi import APIRouter
from src.dto import FetchChatResponse, EventMessage
from google.adk.sessions import DatabaseSessionService
from typing import List, Optional
from fastapi import Form
from src.config import database_settings, app_settings
import logging
from google.adk.sessions import Session
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fetchchat", tags=["FetchChat"])

db_session_service = DatabaseSessionService(
    db_url=database_settings.dsn, 
)

@router.post("", response_model=FetchChatResponse)
async def fetch_chat(
    user_id: str = Form(...),
    session_id: Optional[str] = Form(None),
):

    logger.info(
        f"📖 Fetching chat history for user_id={user_id}, session_id={session_id}"
    )  # Pour test

    session = await db_session_service.get_session(
        app_name=app_settings.APP_NAME, user_id=user_id, session_id=session_id
    )

    logger.info(f"Nombre d'événements dans la session: {len(session.events) if session else 'N/A'}")

    if not session:
        logger.warning("❌ Session not found")
        return FetchChatResponse(
            session_id=session_id, user_id=user_id, messages=[]
        )

    messages: List[EventMessage] = []

    for e in session.events:
        # Récupération sécurisée des infos de chaque event
        evt_type = getattr(e, "event_type", "unknown")
        payload = getattr(e, "payload", {}) or {}

        # Certains events ADK contiennent le texte dans content.parts[0].text
        text = None
        if isinstance(payload, dict) and "text" in payload:
            text = payload.get("text")
        elif hasattr(e, "content") and getattr(e.content, "parts", None):
            parts = getattr(e.content, "parts", [])
            if parts and hasattr(parts[0], "text"):
                text = parts[0].text

        messages.append(
            EventMessage(
                type=evt_type, text=text, timestamp=getattr(e, "timestamp", None)
            )
        )

    logger.info(f"✅ Retrieved {len(messages)} events with text")
    for msg in messages:
        logger.info(f" - [{msg.type}] {msg.text}")

    return FetchChatResponse(
        session_id=session.id, user_id=session.user_id, messages=messages
    )
