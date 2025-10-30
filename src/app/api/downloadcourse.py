"""Endpoint to download a course as PDF."""

import json
import logging

from fastapi import APIRouter, Form, HTTPException

from src.bdd import DBManager
from src.models import CourseOutput
from src.utils.save_files import generate_course_pdf_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloadcourse", tags=["DownloadCourse"])


@router.post("")
async def download_course(
    session_id: str = Form(...),
):
    """Download a course as PDF by session ID."""
    try:
        dbmanager = DBManager()
        test_course = await dbmanager.get_document_by_session_id(session_id)

        if not test_course:
            logger.warning(f"No course found for session_id: {session_id}")
            raise HTTPException(
                status_code=404, detail="Course not found for this session_id"
            )

        contenu = test_course.get("contenu")

        # If content is a JSON string, parse it
        if isinstance(contenu, str):
            course_data = json.loads(contenu)
        else:
            course_data = contenu

        objet_course = CourseOutput.model_validate(course_data)

        return generate_course_pdf_response(objet_course)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        raise HTTPException(
            status_code=500, detail="Error parsing course content"
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error generating PDF: {str(e)}"
        )
