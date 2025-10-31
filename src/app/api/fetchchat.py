"""Endpoint to fetch chat history for a session."""

import logging
from typing import List, Optional, Literal, cast

from fastapi import APIRouter, Form
from google.adk.sessions import DatabaseSessionService

from src.config import app_settings, database_settings
from src.dto import EventMessage, FetchChatResponse

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
    """Fetch chat history for a given session."""
    logger.info(
        f"Fetching chat history for user_id={user_id}, session_id={session_id}"
    )

    session = None

    if session_id:

        session = await db_session_service.get_session(
            app_name=app_settings.APP_NAME, user_id=user_id, session_id=session_id
        )

        logger.info(f"Number of events in session: {len(session.events) if session else 'N/A'}")

    if not session:
        logger.warning("Session not found")
        return FetchChatResponse(
            session_id=session_id, user_id=user_id, messages=[]
        )

    messages: List[EventMessage] = []

    for e in session.events:
        # Safe retrieval of event information
        evt_type_raw = getattr(e, "event_type", "unknown")
        payload = getattr(e, "payload", {}) or {}

        # Normalize event type to accepted literal values
        valid_types = {"user", "bot", "system", "unknown"}
        evt_type: Literal["user", "bot", "system", "unknown"] = cast(
            Literal["user", "bot", "system", "unknown"],
            evt_type_raw if isinstance(evt_type_raw, str) and evt_type_raw in valid_types
            else "unknown"
        )

        # Some ADK events contain text in content.parts[0].text
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

    logger.info(f"Retrieved {len(messages)} events with text")
    for msg in messages:
        logger.info(f" - [{msg.type}] {msg.text}")

    return FetchChatResponse(
        session_id=session.id, 
        user_id=session.user_id, 
        messages=messages
    )
