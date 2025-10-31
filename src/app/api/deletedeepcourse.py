"""Endpoint to delete a deep course."""

import logging

from fastapi import APIRouter, Form

from src.bdd import DBManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deletedeepcourse", tags=["DeleteDeepCourse"])


@router.delete("", status_code=204)
async def delete_deepcourse(user_id: str = Form(...), deepcourse_id: str = Form(...)):
    """Delete a deep course for a user."""
    db_manager = DBManager()
    logger.info(f"Deleting deepcourse_id={deepcourse_id} for user_id={user_id}")

    await db_manager.delete_deepcourse(user_id, deepcourse_id)
    logger.info(f"deepcourse_id={deepcourse_id} deleted for user_id={user_id}")
    return {"status": "deleted", "deepcourse_id": deepcourse_id, "user_id": user_id}