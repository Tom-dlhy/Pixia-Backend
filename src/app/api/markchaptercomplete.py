from fastapi import APIRouter
from src.dto import MarkChapterRequest, MarkChapterResponse
from src.bdd import DBManager

router = APIRouter(prefix="/markchaptercomplete", tags=["MarkChapterComplete"])

@router.put("", response_model=MarkChapterResponse)
async def mark_chapter_complete(req: MarkChapterRequest):
    db_manager = DBManager()
    await db_manager.mark_chapter_complete(req.chapter_id)
    return MarkChapterResponse(is_complete=True)
