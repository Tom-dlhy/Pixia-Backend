from fastapi import APIRouter, Form
from src.bdd import DBManager
from pydantic import BaseModel
from typing import List
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/fetchalldeepcourses", tags=["FetchAllDeepCourses"])


class DeepCourseResponse(BaseModel):
    deepcourse_id: str
    title: str
    completion: float


class FetchAllChatDeepCoursesResponse(BaseModel):
    sessions: List[DeepCourseResponse]


@router.post("", response_model=FetchAllChatDeepCoursesResponse)
async def fetch_all_deepcourses(user_id: str = Form(...)):
    """
    Récupère tous les deep courses pour un utilisateur avec leur taux de complétion.
    """
    db_manager = DBManager()
    logger.info(f"📚 Fetching all deepcourses for user_id={user_id}")
    
    deep_courses_data = await db_manager.fetch_all_deepcourses(user_id)

    all_deepcourses = [
        DeepCourseResponse(
            deepcourse_id=deepcourse.get("deepcourse_id", ""),
            title=deepcourse.get("title", ""),
            completion=deepcourse.get("completion", 0.0)
        )
        for deepcourse in deep_courses_data
    ]

    logger.info(f"✅ {len(all_deepcourses)} deepcourses récupérés")
    return FetchAllChatDeepCoursesResponse(sessions=all_deepcourses)

