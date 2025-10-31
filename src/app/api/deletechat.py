"""Endpoint to delete a chat session."""

from fastapi import APIRouter, status
from google.adk.sessions import DatabaseSessionService

from src.bdd import DBManager
from src.config import app_settings
from src.dto import DeleteChatRequest


router = APIRouter(prefix="/deletechat", tags=["DeleteChat"])


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(req: DeleteChatRequest):
    """Delete a chat session and associated data."""
    db_manager = DBManager()
    #session_service = DatabaseSessionService() 
    app_name = app_settings.APP_NAME

    # await db_manager.delete_chat(req.session_id)
    
    # await session_service.delete_session(app_name, req.user_id, req.session_id)

    # TODO :implement

    return status.HTTP_204_NO_CONTENT
