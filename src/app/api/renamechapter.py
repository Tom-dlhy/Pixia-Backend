from fastapi import APIRouter
from src.dto import RenameChapterRequest, RenameChapterResponse
from src.bdd import DBManager

router = APIRouter(prefix="/renamechapter", tags=["RenameChapter"])

@router.put("", response_model=RenameChapterResponse)
async def rename_chapter(req: RenameChapterRequest):
    db_manager = DBManager()
    await db_manager.rename_chapter(req.chapter_id, req.title)
    return RenameChapterResponse(chapter_id=req.chapter_id, title=req.title)
