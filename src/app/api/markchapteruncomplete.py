from fastapi import APIRouter
from src.dto import MarkChapterRequest, MarkChapterResponse
from src.bdd import DBManager

router = APIRouter(prefix="/markchapteruncomplete", tags=["MarkChapterUncomplete"])

@router.put("", response_model=MarkChapterResponse)
async def mark_chapter_uncomplete(req: MarkChapterRequest):
    db_manager = DBManager()
    await db_manager.mark_chapter_uncomplete(req.chapter_id)
    return MarkChapterResponse(is_complete=False)
