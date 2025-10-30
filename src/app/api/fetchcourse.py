"""Endpoint to fetch a course for a session."""

import json
import logging

from fastapi import APIRouter, Form

from src.bdd import DBManager
from src.models import CourseOutput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fetchcourse", tags=["FetchCourse"])


@router.post("", response_model=CourseOutput)
async def fetch_course(
    session_id: str = Form(...),
):
    """Fetch a course for a given session from the database."""
    bdd_manager = DBManager()

    logger.info(f"Fetching course for session_id={session_id}")

    # Retrieve document from database
    try:
        course_object = await bdd_manager.get_document_by_session_id(session_id)
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        return CourseOutput(id=session_id, title="", parts=[])

    # Check if document exists
    if not course_object:
        logger.warning(f"No document found for session_id={session_id}")
        return CourseOutput(id=session_id, title="", parts=[])

    # Extract stored JSON content
    try:
        contenu = course_object.get("contenu")

        # If content is a JSON string, parse it
        if isinstance(contenu, str):
            course_data = json.loads(contenu)
        else:
            course_data = contenu

        # Ensure course_data is a dict before processing
        if not isinstance(course_data, dict):
            logger.warning(f"Invalid course data format for session_id={session_id}")
            return CourseOutput(id=session_id, title="", parts=[])

        # Add ID if missing
        if "id" not in course_data:
            course_data["id"] = session_id

        logger.info(f"Retrieved course for session_id={session_id}")
        return CourseOutput.model_validate(course_data)

    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing course content: {e}")
        return CourseOutput(id=session_id, title="", parts=[])
