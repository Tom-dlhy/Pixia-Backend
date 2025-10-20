from fastapi import APIRouter
from src.dto import FetchChatRequest, FetchChatResponse
from src.bdd import DBManager
from google.adk.sessions import DatabaseSessionService

router = APIRouter(prefix="/fetchchats", tags=["FetchChats"])

@router.post("", response_model=FetchChatResponse)
async def fetch_chat(req: FetchChatRequest):
    db_manager = DBManager()
    sessions = await db_manager.fetch_all_chats(req.user_id)
    response = FetchChatResponse(sessions=listed_sessions)
    return response
