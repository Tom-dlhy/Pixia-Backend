from pydantic import BaseModel, Field
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
from src.models import GenerativeToolOutput
from src.config import database_settings, app_settings
from google.adk.sessions.database_session_service import DatabaseSessionService
from src.bdd import DBManager
from src.utils import get_deep_course_id,get_user_id

logger = logging.getLogger(__name__)


async def generate_new_chapter(description_user: str) -> GenerativeToolOutput:
    """Generate a Chapter from a DeepCourse synthesis description."""
    deepcourse_id = get_deep_course_id()
    user_id = get_user_id()

    db_session_service = DatabaseSessionService(
        db_url=database_settings.dsn,
    )

    db_manager = DBManager()

    logger.info(
        f"🔄 Génération d'un nouveau chapitre pour deepcourse_id={deepcourse_id}"
    )

    # Récupérer les informations du deepcourse et des chapitres existants
    try:
        deepcourse_data_list: List[Dict[str, Any]] = (
            await db_manager.get_deepcourse_and_chapter_with_id(deepcourse_id)
        )
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du deepcourse: {e}")
        raise

    if not deepcourse_data_list:
        logger.error(f"❌ Aucun deepcourse trouvé pour l'ID: {deepcourse_id}")
        raise ValueError(f"DeepCourse {deepcourse_id} not found")

    # Extraire le titre du deepcourse (premier élément) et tous les chapitres
    first_item = deepcourse_data_list[0]
    deepcourse_title = (
        first_item.get("deepcourse_title", "") if isinstance(first_item, dict) else ""
    )

    # Construire le contexte pour Gemini
    lines = [f"Titre du Deepcourse : {deepcourse_title}"]
    for idx, chapter_data in enumerate(deepcourse_data_list, start=1):
        chapter_title = (
            chapter_data.get("chapter_title", "")
            if isinstance(chapter_data, dict)
            else str(chapter_data)
        )
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
                synthesis_chapter = ChapterSynthesis.model_validate(
                    cast(dict, parsed_data)
                )
        else:
            payload = getattr(response, "text", None)
            if isinstance(payload, str):
                synthesis_chapter = ChapterSynthesis.model_validate_json(payload)
            else:
                synthesis_chapter = ChapterSynthesis.model_validate(payload)

        logger.info(
            f"✅ Synthèse du chapitre générée: {synthesis_chapter.chapter_title}"
        )
    except Exception as err:
        logger.error(f"❌ Erreur lors de la génération de la synthèse: {err}")
        raise

    # Générer les trois composantes du chapitre
    logger.info("⏳ Génération des exercices, cours et évaluation...")
    try:
        # Import local pour éviter les cycles d'importation
        from src.tools.exercises_tools import generate_exercises
        from src.tools.cours_tools import generate_courses

        # Paralléliser les 3 générations
        exercise_result, course_result, evaluation_result = await asyncio.gather(
            generate_exercises(is_called_by_agent=False,synthesis= synthesis_chapter.synthesis_exercise),
            generate_courses(is_called_by_agent=False,course_synthesis= synthesis_chapter.synthesis_course),
            generate_exercises(is_called_by_agent=False,synthesis= synthesis_chapter.synthesis_evaluation),
        )
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération des composantes: {e}")
        raise

    if isinstance(exercise_result, ExerciseOutput) and isinstance(course_result, CourseOutput) and isinstance(evaluation_result, ExerciseOutput):
        exercice = exercise_result
        course = course_result
        evaluation = evaluation_result

    # Créer et retourner le Chapter
    chapter_id = str(uuid4())
    chapter = Chapter(
        id_chapter=chapter_id,
        title=synthesis_chapter.chapter_title,
        course=course,
        exercice=exercice,
        evaluation=evaluation,
    )

    agent = "deep-course-chapter"
    redirect_id = None
    completed = False

    if isinstance(chapter, Chapter) and user_id is not None and deepcourse_id is not None:
        try:
            session_exercise = (
                await db_session_service.create_session(
                    app_name=app_settings.APP_NAME,
                    user_id=user_id,
                )
            )
            session_course = (
                await db_session_service.create_session(
                    app_name=app_settings.APP_NAME,
                    user_id=user_id,
                )
            )
            session_evaluation = (
                await db_session_service.create_session(
                    app_name=app_settings.APP_NAME,
                    user_id=user_id,
                )
            )
            await db_manager.store_chapter(
                title=chapter.title,
                user_id=user_id,
                deepcourse_id=deepcourse_id,
                chapter_id=chapter.id_chapter,
                session_exercise=session_exercise.id,
                session_course=session_course.id,
                session_evaluation=session_evaluation.id,
                exercice=chapter.exercice,
                course=chapter.course,
                evaluation=chapter.evaluation,
            )
            agent = "deep-course"
            redirect_id = chapter.id_chapter
            completed = True
            logger.info(
                f"✅ Chapter stocké avec succès : {chapter.id_chapter}"
            )
        except Exception as e:
            logger.error(
                f"❌ Erreur lors du stockage du chapitre: {e}"
            )
            raise
    else:
        logger.warning(
            f"⚠️ Chapter validé mais pas une instance de Chapter"
        )

    logger.info(f"✅ Chapitre créé avec succès: {chapter_id}")

    return GenerativeToolOutput(
        agent=agent,
        redirect_id=redirect_id,
        completed=completed
    )
