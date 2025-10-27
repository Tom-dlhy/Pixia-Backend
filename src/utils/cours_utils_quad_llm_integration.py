"""
Intégration du pipeline Quad LLM dans la génération de cours.

Ce module remplace la génération simple de parties (1 LLM) par un pipeline
dual-LLM spécialisé avec sélection intelligente du type de diagramme.

Pipeline:
1. LLM #1: Génère le contenu markdown + sélectionne le type de diagramme (4 types)
   pour TOUTES les parties d'un coup
2. LLM #2 (spécialisé) EN PARALLÈLE: Génère le code du diagramme avec retry jusqu'à 3 tentatives
3. Kroki EN PARALLÈLE: Convertit le code en PNG base64
4. CourseOutput: Retourne le cours complet avec contenu, diagram_type, diagram_code, img_base64
"""

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
        course_synthesis = CourseSynthesis.model_validate(course_synthesis)

    try:
        # Utiliser le pipeline Quad LLM existant (optimisé)
        # Ce pipeline génère déjà la structure complète du cours
        result = await generate_course_complete(course_synthesis)

        if not result:
            logger.error(f"[PIPELINE] Pipeline Quad LLM a échoué - result is None")
            # Re-lever l'exception pour que le caller la gère
            raise ValueError("Pipeline Quad LLM failed: no result")

        if not isinstance(result, CourseOutput):
            logger.error(
                f"[PIPELINE] Pipeline Quad LLM a échoué - mauvais type: {type(result)}"
            )
            raise ValueError(f"Pipeline Quad LLM failed: wrong type {type(result)}")

        return result

    except Exception as e:
        logger.error(f"[PIPELINE] ❌ Erreur: {e}", exc_info=True)
        # Re-lever pour que le caller gère l'erreur proprement
        raise
