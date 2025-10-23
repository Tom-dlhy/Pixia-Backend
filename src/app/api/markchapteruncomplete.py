from fastapi import APIRouter, Form
from src.dto import MarkChapterRequest, MarkChapterResponse
from src.bdd import DBManager

router = APIRouter(prefix="/markchapteruncomplete", tags=["MarkChapterUncomplete"])

@router.put("")
async def mark_chapter_uncomplete(chapter_id: str = Form(...)):
    db_manager = DBManager()
    await db_manager.mark_chapter_uncomplete(chapter_id)
    return {"is_complete": False}
