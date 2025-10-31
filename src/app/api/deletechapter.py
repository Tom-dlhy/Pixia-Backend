"""Endpoint to delete a chapter."""

from fastapi import APIRouter, status

from src.bdd import DBManager
from src.config import app_settings
from src.dto import DeleteChapterRequest

router = APIRouter(prefix="/deletechapter", tags=["DeleteChapter"])


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chapter(req: DeleteChapterRequest):
    """Delete a chapter and associated documents."""
    db_manager = DBManager()
    app_name = app_settings.APP_NAME

    await db_manager.delete_chapter(req.chapter_id)

    list_session_ids = await db_manager.get_session_from_document(req.chapter_id)
    
    await db_manager.delete_document_for_chapter(req.chapter_id)

    return status.HTTP_204_NO_CONTENT
