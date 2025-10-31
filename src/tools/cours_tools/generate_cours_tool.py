"""Course generation tool with dual-LLM pipeline.

Generates complete courses with dual-LLM architecture for content and diagrams.
"""

import json
import logging
from typing import Union
from uuid import uuid4

from google.adk.sessions.database_session_service import DatabaseSessionService

from src.bdd import DBManager
from src.config import app_settings, database_settings
from src.models import CourseOutput, CourseSynthesis, GenerativeToolOutput
from src.utils import get_user_id
from src.utils.cours_utils_quad_llm_integration import generate_courses_quad_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_courses(
    is_called_by_agent: bool, course_synthesis: CourseSynthesis
) -> Union[GenerativeToolOutput, CourseOutput]:
    """Génère un cours complet.

    Processus:
    1. Validation du CourseSynthesis (description, difficulty, level_detail)
    2. Appel du planner pour générer la structure du cours (CoursePlan)
    3. Génération PARALLÈLE de toutes les parties avec Quad LLM:
       - LLM #1: Contenu markdown + sélection type diagramme (4 types)
       - LLM #2 (spécialisé): Code diagramme selon le type (max 3 retries)
       - Kroki: Conversion en PNG base64
    4. Retour du CourseOutput avec contenu markdown + diagrammes

    Args:
        is_called_by_agent: Si appelé par un agent (affecte le format de retour)
        course_synthesis: CourseSynthesis avec description, difficulty, level_detail

    Returns:
        CourseOutput ou GenerativeToolOutput si appelé par un agent.
    """
    if isinstance(course_synthesis, dict):
        course_synthesis = CourseSynthesis.model_validate(course_synthesis)

    db_session_service = DatabaseSessionService(
        db_url=database_settings.dsn,
    )
    bdd_manager = DBManager()

    agent = None
    redirect_id = None
    completed = False

    result = await generate_courses_quad_llm(course_synthesis)

    logger.info("[GENERATE_COURSES] Course generated successfully")

    # Storage

    if is_called_by_agent:
        if user_id := get_user_id():
            copilote_session_id = str(uuid4())
            await db_session_service.create_session(
                session_id=copilote_session_id,
                app_name=app_settings.APP_NAME,
                user_id=user_id,
            )
            if isinstance(result, CourseOutput):
                await bdd_manager.store_basic_document(
                    content=result,
                    session_id=copilote_session_id,
                    sub=user_id,
                )
                agent = "course"
                redirect_id = copilote_session_id
                completed = True

        return GenerativeToolOutput(
            agent=agent,
            redirect_id=redirect_id,
            completed=completed
        )
    else:
        return result
