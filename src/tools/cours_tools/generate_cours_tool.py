import logging
from src.models.cours_models import CourseSynthesis
from src.utils.cours_utils_quad_llm_integration import generate_courses_quad_llm
import json
from typing import Any, Union


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_courses(course_synthesis: CourseSynthesis) -> Union[dict, Any]:
    """
    Génère un cours complet avec le pipeline Quad LLM spécialisé.

    Processus:
    1. Validation du CourseSynthesis (description, difficulty, level_detail)
    2. Appel du planner pour générer la structure du cours (CoursePlan)
    3. Génération PARALLÈLE de toutes les parties avec Quad LLM:
       - LLM #1: Contenu markdown + sélection type diagramme (4 types)
       - LLM #2 (spécialisé): Code diagramme selon le type (max 3 retries)
       - Kroki: Conversion en SVG base64
    4. Retour du CourseOutput avec contenu markdown + diagrammes

    Args:
        course_synthesis: CourseSynthesis avec description, difficulty, level_detail

    Returns:
        CourseOutput.model_dump() avec toutes les parties complètes
    """
    if isinstance(course_synthesis, dict):
        course_synthesis = CourseSynthesis(**course_synthesis)

    result = await generate_courses_quad_llm(course_synthesis)

    logger.info(f"[GENERATE_COURSES] ✅ Cours généré avec succès")

    return result
