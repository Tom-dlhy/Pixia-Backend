"""
Tool pour la génération de cours via ADK.
Implémentation optimisée: 1 LLM + Parallelisation KROKI avec DEBUG.
"""

import logging
import asyncio
import json
import sys
from typing import Any, Union, Optional
from uuid import uuid4

from src.models.cours_models import CourseSynthesis, CourseOutputWithMermaid
from src.utils.cours_utils_v2 import generate_complete_course, generate_all_schemas

# Setup logging avec flush immédiat
logging.basicConfig(
    level=logging.DEBUG, format="[%(levelname)s] %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def generate_courses(
    course_synthesis: CourseSynthesis,
) -> Union[dict, Any]:
    """
    Génère un cours complet avec schémas Mermaid en parallèle.

    Pipeline optimisé:
    1. LLM génère contenu + code Mermaid d'un coup
    2. Validation du Mermaid
    3. Génération parallèle des schémas via Kroki
    4. Retour du JSON complet

    Args:
        course_synthesis: Synthèse du cours (description, difficulté, niveau de détail)

    Returns:
        dict: JSON du cours complètement généré (contenu + schémas base64)
    """
    try:
        # Validation d'entrée
        if isinstance(course_synthesis, dict):
            logger.debug("[MAIN] Conversion dict → CourseSynthesis")
            course_synthesis = CourseSynthesis(**course_synthesis)

        logger.info("=" * 70)
        logger.info("[MAIN] 🎓 DÉBUT GÉNÉRATION COURS")
        logger.info(f"[MAIN]    Description: {course_synthesis.description[:40]}...")
        logger.info(f"[MAIN]    Difficulté: {course_synthesis.difficulty}")
        logger.info(f"[MAIN]    Niveau: {course_synthesis.level_detail}")
        logger.info("=" * 70)

        # ===== ÉTAPE 1: Génération complète (1 LLM) =====
        logger.info(
            "[MAIN] ⏳ ÉTAPE 1/2: Génération contenu + Mermaid (1 appel LLM)..."
        )
        course_output = await asyncio.to_thread(
            generate_complete_course, course_synthesis
        )

        if not course_output:
            logger.error("[MAIN] ❌ Échec génération du cours (LLM)")
            return {"error": "Failed to generate course content"}

        logger.info(
            f"[MAIN] ✅ ÉTAPE 1 OK: {len(course_output.parts)} parties générées"
        )
        logger.info(f"[MAIN]    Titre: {course_output.title}")

        # ===== ÉTAPE 2: Génération parallèle des schémas =====
        logger.info(
            "[MAIN] ⏳ ÉTAPE 2/2: Génération parallèle schémas Mermaid via Kroki..."
        )
        course_output = await generate_all_schemas(course_output)
        logger.info("[MAIN] ✅ ÉTAPE 2 OK: Tous les schémas générés")

        # ===== ÉTAPE 3: Conversion en dict =====
        logger.debug("[MAIN] Conversion en dict...")
        course_dict = course_output.model_dump()

        logger.info("=" * 70)
        logger.info(f"[MAIN] ✅✅✅ GÉNÉRATION COMPLÉTÉE AVEC SUCCÈS")
        logger.info(f"[MAIN]    {len(course_output.parts)} parties générées")
        logger.info("=" * 70)

        return course_dict

    except Exception as e:
        logger.error(f"[MAIN] ❌ Erreur fatale: {e}", exc_info=True)
        return {"error": str(e)}


# ================= FONCTION WRAPPER POUR ADK =================

def generate_courses_sync(course_synthesis: Union[dict, CourseSynthesis]) -> dict:
    """
    Wrapper synchrone pour utilisation avec ADK agents.
    ADK exécute dans un event loop, cette fonction l'utilise.

    Args:
        course_synthesis: Synthèse du cours

    Returns:
        dict: Résultat de la génération
    """
    try:
        # Essaie d'utiliser l'event loop existant
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si une boucle tourne déjà, crée une tâche
            return asyncio.run_coroutine_threadsafe(
                generate_courses(course_synthesis), loop
            ).result()
        else:
            # Sinon, utilise asyncio.run()
            return asyncio.run(generate_courses(course_synthesis))
    except RuntimeError:
        # Pas de boucle d'événement, en crée une
        return asyncio.run(generate_courses(course_synthesis))
