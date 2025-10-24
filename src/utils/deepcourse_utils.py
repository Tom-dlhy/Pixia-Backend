import asyncio
import logging
from uuid import uuid4
from typing import Dict, List, Union, Any, cast

from src.models import (
    Chapter,
    ChapterSynthesis,
    CourseOutput,
    DeepCourseSynthesis,
    ExerciseOutput,
    DeepCourseOutput,
)
from src.config import gemini_settings
from src.prompts import SYSTEM_PROMPT_GENERATE_NEW_CHAPTER
from src.bdd import DBManager

logger = logging.getLogger(__name__)


async def generate_new_chapter(deepcourse_id: str, description_user: str) -> Chapter:
    """Generate a Chapter from a DeepCourse synthesis description."""
    
    db_manager = DBManager()
    
    logger.info(f"🔄 Génération d'un nouveau chapitre pour deepcourse_id={deepcourse_id}")
    
    # Récupérer les informations du deepcourse et des chapitres existants
    try:
        deepcourse_data_list: List[Dict[str, Any]] = await db_manager.get_deepcourse_and_chapter_with_id(deepcourse_id)
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du deepcourse: {e}")
        raise

    if not deepcourse_data_list:
        logger.error(f"❌ Aucun deepcourse trouvé pour l'ID: {deepcourse_id}")
        raise ValueError(f"DeepCourse {deepcourse_id} not found")

    # Extraire le titre du deepcourse (premier élément) et tous les chapitres
    first_item = deepcourse_data_list[0]
    deepcourse_title = first_item.get("deepcourse_title", "") if isinstance(first_item, dict) else ""
    
    # Construire le contexte pour Gemini
    lines = [f"Titre du Deepcourse : {deepcourse_title}"]
    for idx, chapter_data in enumerate(deepcourse_data_list, start=1):
        chapter_title = chapter_data.get("chapter_title", "") if isinstance(chapter_data, dict) else str(chapter_data)
        lines.append(f"Titre du chapitre numero {idx} : {chapter_title}")
    
    context_text = "\n".join(lines)
    
    logger.debug(f"📋 Contexte généré:\n{context_text}")

    # Appel à Gemini pour générer la synthèse du chapitre
    try:
        response = await gemini_settings.CLIENT.aio.models.generate_content(
            model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
            contents=f"{SYSTEM_PROMPT_GENERATE_NEW_CHAPTER}\n{context_text}\nDescription de la demande utilisateur : {description_user}",
            config={
                "response_mime_type": "application/json",
                "response_schema": ChapterSynthesis,
            },
        )

        if hasattr(response, "parsed") and response.parsed:
            parsed_data = response.parsed
            if isinstance(parsed_data, ChapterSynthesis):
                synthesis_chapter = parsed_data
            elif isinstance(parsed_data, dict):
                synthesis_chapter = ChapterSynthesis.model_validate(parsed_data)
            else:
                # Cast to dict for validation (Gemini returns dict or BaseModel)
                synthesis_chapter = ChapterSynthesis.model_validate(cast(dict, parsed_data))
        else:
            payload = getattr(response, "text", None)
            if isinstance(payload, str):
                synthesis_chapter = ChapterSynthesis.model_validate_json(payload)
            else:
                synthesis_chapter = ChapterSynthesis.model_validate(payload)
        
        logger.info(f"✅ Synthèse du chapitre générée: {synthesis_chapter.chapter_title}")
    except Exception as err:
        logger.error(f"❌ Erreur lors de la génération de la synthèse: {err}")
        raise

    # Générer les trois composantes du chapitre
    logger.info("⏳ Génération des exercices, cours et évaluation...")
    try:
        # Import local pour éviter les cycles d'importation
        from src.tools.exercises_tools import generate_exercises
        from src.tools.cours_tools import generate_courses
        
        exercise_result = await generate_exercises(synthesis_chapter.synthesis_exercise)
        course_result = await generate_courses(synthesis_chapter.synthesis_course)
        evaluation_result = await generate_exercises(synthesis_chapter.synthesis_evaluation)
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération des composantes: {e}")
        raise

    # Valider et convertir les résultats
    try:
        exercice = (
            ExerciseOutput.model_validate(exercise_result)
            if isinstance(exercise_result, dict)
            else exercise_result
        )
        course = (
            CourseOutput.model_validate(course_result)
            if isinstance(course_result, dict)
            else course_result
        )
        evaluation = (
            ExerciseOutput.model_validate(evaluation_result)
            if isinstance(evaluation_result, dict)
            else evaluation_result
        )
        logger.info("✅ Tous les résultats validés avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la validation des résultats: {e}")
        raise

    # Créer et retourner le Chapter
    chapter_id = str(uuid4())
    chapter = Chapter(
        id_chapter=chapter_id,
        title=synthesis_chapter.chapter_title,
        course=course,
        exercice=exercice,
        evaluation=evaluation,
    )
    
    logger.info(f"✅ Chapitre créé avec succès: {chapter_id}")
    return chapter