"""Endpoint to fetch an exercise for a session."""

import json
import logging

from fastapi import APIRouter, Form

from src.bdd import DBManager
from src.models import ExerciseOutput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fetchexercise", tags=["FetchExercise"])


@router.post("", response_model=ExerciseOutput)
async def fetch_exercise(
    session_id: str = Form(...),
):
    """Fetch an exercise for a given session from the database."""
    bdd_manager = DBManager()

    logger.info(f"Fetching exercise for session_id={session_id}")

    # Retrieve document from database
    try:
        exo_data = await bdd_manager.get_document_by_session_id(session_id)
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        return ExerciseOutput(id=session_id, exercises=[], title="")

    # Check if document exists
    if not exo_data:
        logger.warning(f"No document found for session_id={session_id}")
        return ExerciseOutput(id=session_id, exercises=[], title="")

    # Extract stored JSON content
    try:
        contenu = exo_data.get("contenu")
        if contenu:

            # If content is a JSON string, parse it
            if isinstance(contenu, str):
                exercise_data = json.loads(contenu)
            else:
                exercise_data = contenu

            # Add ID if missing
            if "id" not in exercise_data.keys():
                exercise_data["id"] = session_id

            # Add title if missing
            if "title" not in exercise_data.keys():
                exercise_data["title"] = ""

            logger.info(f"Retrieved exercise for session_id={session_id}")
            return ExerciseOutput.model_validate(exercise_data)

    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
        logger.error(f"Error parsing exercise content: {e}")
        return ExerciseOutput(id=session_id, exercises=[], title="")
