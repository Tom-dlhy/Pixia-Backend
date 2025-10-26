import asyncio
import json
import logging
from typing import Any, Union
from uuid import uuid4

from src.models.cours_models import CourseSynthesis, CourseOutput
from src.utils.cours_utils_quad_llm import generate_course_complete


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_courses_quad_llm(
    course_synthesis: Any,
    planner_func=None,
) -> CourseOutput:
    """
    Génère un cours complet avec le pipeline Quad LLM dual-LLM spécialisé.

    Processus:
    1. ADK agent obtient CourseSynthesis avec description, difficulty, level_detail
    2. Pipeline Quad LLM (optimisé):
       - LLM #1: Génère contenu + types de diagramme pour TOUTES les parties
       - EN PARALLÈLE pour chaque partie:
         * LLM #2 (spécialisé): Code diagramme selon le type (max 3 retries)
         * Kroki: PNG base64
    3. CourseOutput retourné avec contenu markdown + diagrams complets

    Note: Le planner n'est pas utilisé directement car LLM #1 génère déjà la structure.
    Pour intégration avec planner existant, voir generate_courses_with_planner().

    Args:
        course_synthesis: CourseSynthesis avec description, difficulty, level_detail
        planner_func: Optionnel (non utilisé dans ce pipeline)

    Returns:
        CourseOutput.model_dump() avec toutes les parties générées
    """
    if isinstance(course_synthesis, dict):
        course_synthesis = CourseSynthesis(**course_synthesis)

    try:
        result = await generate_course_complete(course_synthesis)

        if not result:
            logger.error(f"[PIPELINE] Pipeline Quad LLM a échoué - result is None")
            raise ValueError("Pipeline Quad LLM failed: no result")

        if not isinstance(result, CourseOutput):
            logger.error(
                f"[PIPELINE] Pipeline Quad LLM a échoué - mauvais type: {type(result)}"
            )
            raise ValueError(f"Pipeline Quad LLM failed: wrong type {type(result)}")

        return result

    except Exception as e:
        logger.error(f"[PIPELINE] Erreur: {e}", exc_info=True)
        raise
