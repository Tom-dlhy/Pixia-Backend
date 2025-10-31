"""Endpoint to rename a chapter."""

from fastapi import APIRouter

from src.bdd import DBManager
from src.dto import RenameChapterRequest, RenameChapterResponse

router = APIRouter(prefix="/renamechapter", tags=["RenameChapter"])


@router.put("", response_model=RenameChapterResponse)
async def rename_chapter(req: RenameChapterRequest):
    """Rename a chapter."""
    db_manager = DBManager()
    await db_manager.rename_chapter(req.chapter_id, req.title)
    return RenameChapterResponse(chapter_id=req.chapter_id, title=req.title)
