from fastapi import APIRouter
from src.dto import FetchAllChatsRequest, FetchAllChatsResponse, DisplaySessionsMain
from src.bdd import DBManager

router = APIRouter(prefix="/fetchallchats", tags=["FetchAllChats"])

@router.post("", response_model=FetchAllChatsResponse)
async def fetch_all_chats(req: FetchAllChatsRequest):
    db_manager = DBManager()
    sessions = await db_manager.fetch_all_chats(req.user_id)
    listed_sessions = [DisplaySessionsMain(**session) for session in sessions]
    response = FetchAllChatsResponse(sessions=listed_sessions)
    return response
