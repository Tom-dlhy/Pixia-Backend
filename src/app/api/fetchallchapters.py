"""Endpoint to fetch all chapters for a deep course."""

import logging
from typing import List

from fastapi import APIRouter, Form
from pydantic import BaseModel

from src.bdd import DBManager

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/fetchallchapters", tags=["FetchAllChapters"])


class Chapter(BaseModel):
    chapter_id: str
    title: str | None = None
    is_complete: bool


class FetchAllChaptersResponse(BaseModel):
    chapters: List[Chapter]


@router.post("")
async def fetch_all_chapters(deepcourse_id: str = Form(...)):
    """Fetch all chapters for a deep course."""
    logger.info(f"Fetching all chapters for deep_course_id={deepcourse_id}")
    db_manager = DBManager()
    chapters = await db_manager.fetch_all_chapters(deepcourse_id)
    listed_chapters = [Chapter.model_validate(chapter) for chapter in chapters]
    logger.info(
        f"Retrieved {len(listed_chapters)} chapters for deep_course_id={deepcourse_id}"
    )
    return FetchAllChaptersResponse(chapters=listed_chapters)

