from fastapi import APIRouter, status
from src.dto import DeleteChatRequest
from src.bdd import DBManager
from google.adk.sessions import DatabaseSessionService
from src.config import app_settings


router = APIRouter(prefix="/deletechat", tags=["DeleteChat"])

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(req: DeleteChatRequest):
    db_manager = DBManager()
    session_service = DatabaseSessionService()
    app_name=app_settings.APP_NAME

    await db_manager.delete_chat(req.session_id)
    
    await session_service.delete_session(app_name,req.user_id, req.session_id)

    return status.HTTP_204_NO_CONTENT
