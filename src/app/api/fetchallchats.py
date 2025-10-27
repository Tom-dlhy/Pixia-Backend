from fastapi import APIRouter
from src.bdd import DBManager
from pydantic import BaseModel
from typing import List
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/fetchallchats", tags=["FetchAllChats"])


class Session(BaseModel):
    session_id: str
    title: str | None = None
    document_type: str


class FetchAllChatRequest(BaseModel):
    user_id: str


class FetchAllChatResponse(BaseModel):
    sessions: List[Session]

@router.post("")
async def fetch_all_chats(data: FetchAllChatRequest):
    logger.info(f"📖 Fetching all chats for user_id={data.user_id}")
    db_manager = DBManager()
    sessions = await db_manager.fetch_all_chats(data.user_id)
    listed_sessions = [Session.model_validate(session) for session in sessions]
    logger.info(
        f"✅ Retrieved {len(listed_sessions)} sessions for user_id={data.user_id}"
    )
    return FetchAllChatResponse(sessions=listed_sessions)

