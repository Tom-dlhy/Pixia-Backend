from fastapi import APIRouter, Form
from src.bdd import DBManager

router = APIRouter(prefix="/markchaptercomplete", tags=["MarkChapterComplete"])

@router.put("")
async def mark_chapter_complete(chapter_id: str = Form(...)):
    db_manager = DBManager()
    await db_manager.mark_chapter_complete(chapter_id)
    return {"is_complete": True}
