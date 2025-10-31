"""Endpoint to fetch chapter documents (session IDs)."""

import logging

from fastapi import APIRouter, Form
from pydantic import BaseModel

from src.bdd import DBManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fetchchapterdocument", tags=["FetchChapterDocument"])
    

class FetchChapterDocumentResponse(BaseModel):
    chapter_id: str
    exercice_session_id: str
    course_session_id: str
    evaluation_session_id: str


@router.post("", response_model=FetchChapterDocumentResponse)
async def fetch_chapter_documents(
    chapter_id: str = Form(...),
):
    """Fetch all document session IDs for a chapter."""
    bdd_manager = DBManager()

    logger.info(f"Fetching documents for chapter_id={chapter_id}")

    # Retrieve document IDs from database
    try:
        chapter_data = await bdd_manager.fetch_chapter_documents(chapter_id)
        if chapter_data:
            return FetchChapterDocumentResponse(
                chapter_id=chapter_id,
                exercice_session_id=chapter_data.get("exercice_session_id", ""),
                course_session_id=chapter_data.get("course_session_id", ""),
                evaluation_session_id=chapter_data.get("evaluation_session_id", "")
            )
        else:
            logger.warning(f"No documents found for chapter_id={chapter_id}")
            return FetchChapterDocumentResponse(
                chapter_id=chapter_id,
                exercice_session_id="",
                course_session_id="",
                evaluation_session_id=""
            )
    except Exception as e:
        logger.error(f"Error retrieving chapter documents: {e}")
        return FetchChapterDocumentResponse(
            chapter_id=chapter_id,
            exercice_session_id="",
            course_session_id="",
            evaluation_session_id=""
        )
