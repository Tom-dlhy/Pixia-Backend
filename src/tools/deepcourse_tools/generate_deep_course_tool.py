import asyncio
from src.models import (
    DeepCourseSynthesis,
    DeepCourseOutput,
    Chapter,
    ExerciseOutput,
    CourseOutput,
)
from src.tools.exercises_tools import generate_exercises
from src.tools.cours_tools import generate_courses
from src.utils.timing import Timer
from src.utils import get_user_id
from uuid import uuid4
import json
import logging
import time

from src.config import database_settings, app_settings
from google.adk.sessions.database_session_service import DatabaseSessionService
from src.bdd import DBManager
from src.models import GenerativeToolOutput
from uuid import uuid4

from typing import List, Dict

logger = logging.getLogger(__name__)


async def generate_deepcourse(synthesis: DeepCourseSynthesis) -> GenerativeToolOutput:

    db_session_service = DatabaseSessionService(
        db_url=database_settings.dsn,
    )
    bdd_manager = DBManager()

    agent = "deep-course"
    redirect_id = None
    completed = False

    if isinstance(synthesis, dict):
        synthesis = DeepCourseSynthesis(**synthesis)

    synthesis_chapters = synthesis.synthesis_chapters

    all_tasks = []
    for chapter in synthesis_chapters:
        # Créer les coroutines SANS les attendre
        all_tasks.append(generate_exercises(is_called_by_agent=False,synthesis=chapter.synthesis_exercise))
        all_tasks.append(generate_courses(is_called_by_agent=False,course_synthesis=chapter.synthesis_course))
        all_tasks.append(generate_exercises(is_called_by_agent=False,synthesis=chapter.synthesis_evaluation))

    all_results = await asyncio.gather(*all_tasks)

    chapters = []
    for idx, chapter_synthesis in enumerate(synthesis_chapters):
        with Timer(f"[CH-{idx+1}] Reconstruction"):
            id_chapter = str(uuid4())
            chapter_title = chapter_synthesis.chapter_title

            base_idx = idx * 3
            exercise_result = all_results[base_idx]
            course_result = all_results[base_idx + 1]
            evaluation_result = all_results[base_idx + 2]

            if isinstance(exercise_result, dict):
                exercice = ExerciseOutput.model_validate(exercise_result)
            else:
                exercice = exercise_result

            if isinstance(course_result, dict):
                if (
                    not course_result
                    or "title" not in course_result
                    or "parts" not in course_result
                ):
                    logger.error(f"[CHAPTER-{idx}] Cours invalide: {course_result}")
                course = CourseOutput.model_validate(course_result)
            else:
                course = course_result

            if isinstance(evaluation_result, dict):
                evaluation = ExerciseOutput.model_validate(evaluation_result)
            else:
                evaluation = evaluation_result

            chapter_output = Chapter(
                id_chapter=id_chapter,
                title=chapter_title,
                course=course,
                exercice=exercice,
                evaluation=evaluation,
            )
            chapters.append(chapter_output)
    deepcourse_output = DeepCourseOutput(
        id=str(uuid4()), title=synthesis.title, chapters=chapters
    )


    ### Storage

    if user_id := get_user_id():

        try:
            # Créer les sessions et mapper les IDs pour chaque chapitre
            dict_session: List[Dict[str, str]] = []

            for chapter in deepcourse_output.chapters:
                try:
                    session_exercise = await db_session_service.create_session(
                        app_name=app_settings.APP_NAME,
                        user_id=user_id,
                    )
                    session_course = await db_session_service.create_session(
                        app_name=app_settings.APP_NAME,
                        user_id=user_id,
                    )
                    session_evaluation = await db_session_service.create_session(
                        app_name=app_settings.APP_NAME,
                        user_id=user_id,
                    )

                    chapter_sessions = {
                        "id_chapter": chapter.id_chapter,
                        "session_id_exercise": session_exercise.id,
                        "session_id_course": session_course.id,
                        "session_id_evaluation": session_evaluation.id,
                    }
                    dict_session.append(
                        chapter_sessions
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Erreur lors de la création des sessions pour le chapitre {chapter.id_chapter}: {e}"
                    )
                    raise

            await bdd_manager.store_deepcourse(
                user_id=user_id,
                content=deepcourse_output,
                dict_session=dict_session,
            )
            redirect_id = deepcourse_output.id
            completed = True
        except Exception as e:
            logger.error(
                f"❌ Erreur lors du stockage du deepcourse: {e}"
            )
            raise

    return GenerativeToolOutput(
        agent=agent,
        completed=completed,
        redirect_id=redirect_id
    )
