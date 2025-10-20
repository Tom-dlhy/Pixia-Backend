from fastapi import APIRouter, status
from src.dto import DeleteChapterRequest
from src.bdd import DBManager
from google.adk.sessions import DatabaseSessionService
from src.config import app_settings

router = APIRouter(prefix="/deletechapter", tags=["DeleteChapter"])

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(req: DeleteChapterRequest):
    db_manager = DBManager()
    session_service = DatabaseSessionService()
    app_name=app_settings.APP_NAME

    await db_manager.delete_chapter(req.chapter_id)

    list_session_ids = await db_manager.get_session_from_document(req.chapter_id)
    
    await db_manager.delete_document_for_chapter(req.chapter_id)

    for session_id in list_session_ids:
        await db_manager.delete_session_title(session_id)
        await session_service.delete_session(app_name, req.user_id, session_id)

    return status.HTTP_204_NO_CONTENT
