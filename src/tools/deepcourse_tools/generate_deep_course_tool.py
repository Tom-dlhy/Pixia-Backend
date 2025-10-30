"""DeepCourse generation tool with parallel task orchestration.

Generates complete deepcourses with all chapters, exercises, and evaluations
using parallel execution and database persistence.
"""

import asyncio
import logging
import time
from typing import Dict, List, Union
from uuid import uuid4

from google.adk.sessions.database_session_service import DatabaseSessionService

from src.bdd import DBManager
from src.config import app_settings, database_settings
from src.models import (
    Chapter,
    CourseOutput,
    DeepCourseOutput,
    DeepCourseSynthesis,
    ExerciseOutput,
)
from src.tools.cours_tools import generate_courses
from src.tools.exercises_tools import generate_exercises
from src.utils import get_user_id
from src.utils.timing import Timer

logger = logging.getLogger(__name__)


async def generate_deepcourse(synthesis: Union[dict, DeepCourseSynthesis]) -> GenerativeToolOutput: # type: ignore
    """
    Génère un deepcourse complet avec tous ses chapitres, exercices et évaluations.

    Args:
        synthesis: Objet DeepCourseSynthesis contenant:
            - title: Titre du deepcourse
            - synthesis_chapters: Liste des chapitres (1-16) avec structure complète

    Returns:
        GenerativeToolOutput avec agent, completed, redirect_id

    Utilisation:
        Appelle ce tool une fois que l'utilisateur a validé le plan du deepcourse.
        Le tool génère en parallèle tous les cours, exercices et évaluations.
    """
    logger.info("[GENERATE_DEEPCOURSE] Tool called!")

    if isinstance(synthesis, dict):
        logger.info("Converting dict → DeepCourseSynthesis...")
        synthesis = DeepCourseSynthesis.model_validate(synthesis)
        logger.info("DeepCourseSynthesis validated from dict")

        logger.info(f"Title: {synthesis.title}")
        logger.info(f"Chapters: {len(synthesis.synthesis_chapters)}")

    db_session_service = DatabaseSessionService(
        db_url=database_settings.dsn,
    )
    bdd_manager = DBManager()

    agent = "deep-course"
    redirect_id = None
    completed = False

    start_time = time.time()

    synthesis_chapters = synthesis.synthesis_chapters
    num_chapters = len(synthesis_chapters)

    task_creation_start = time.time()
    all_tasks = []
    task_descriptions = []

    for idx, chapter in enumerate(synthesis_chapters):
        logger.info(f"Chapter {idx + 1}: {chapter.chapter_title}")

        logger.info(f"├─ Exercises: {chapter.synthesis_exercise.title}")
        all_tasks.append(
            generate_exercises(
                is_called_by_agent=False, synthesis=chapter.synthesis_exercise
            )
        )
        task_descriptions.append(f"CH{idx + 1}-Exercises")

        logger.info(f"├─ Course")
        all_tasks.append(
            generate_courses(
                is_called_by_agent=False, course_synthesis=chapter.synthesis_course
            )
        )
        task_descriptions.append(f"CH{idx + 1}-Course")

        logger.info(f"└─ Evaluation: {chapter.synthesis_evaluation.title}")
        all_tasks.append(
            generate_exercises(
                is_called_by_agent=False, synthesis=chapter.synthesis_evaluation
            )
        )
        task_descriptions.append(f"CH{idx + 1}-Evaluation")

    task_creation_time = time.time() - task_creation_start
    logger.info(f"Created {len(all_tasks)} tasks in {task_creation_time:.2f}s")

    logger.info("Starting parallel execution...")
    logger.info(f"Task timeout: 180s (3 min)")
    logger.info(f"Total tasks: {len(all_tasks)}")

    execution_start = time.time()
    try:
        # Use asyncio.wait_for for global timeout on all tasks
        # Timeout = 60s per task * nb_chapters * 3 + buffer
        timeout_per_task = 180  # 3 min per task (exercise/course/evaluation)
        total_timeout = timeout_per_task * num_chapters + 60  # +60s buffer
        logger.info(f"Global timeout: {total_timeout}s for {num_chapters} chapter(s)")

        all_results = await asyncio.wait_for(
            asyncio.gather(*all_tasks, return_exceptions=False),
            timeout=total_timeout,
        )
        logger.info("All tasks completed successfully")
    except asyncio.TimeoutError as te:
        logger.error(f"TIMEOUT during parallel execution after {total_timeout}s")
        logger.error(f"Completed tasks: {num_chapters * 3} expected")
        logger.error("This error typically occurs with:")
        logger.error("- Very large deepcourses (>8 chapters)")
        logger.error("- Very detailed content (level_detail=detailed)")
        logger.error("- Gemini API rate limiting")
        raise RuntimeError(
            f"Timeout deepcourse: {num_chapters} chapters too heavy or API rate-limited"
        )
    except Exception as e:
        logger.error(f"ERROR during parallel execution: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("This may indicate credentials issue or API limit")
        raise

    execution_time = time.time() - execution_start
    logger.info(
        f"Parallel execution: {execution_time:.2f}s ({num_chapters * 3} tasks)"
    )

    # Rebuild results by chapter
    rebuild_start = time.time()
    chapters = []
    for idx, chapter_synthesis in enumerate(synthesis_chapters):
        with Timer(f"[CH-{idx + 1}] Reconstruction"):
            id_chapter = str(uuid4())
            chapter_title = chapter_synthesis.chapter_title

            # Get results for this chapter (3 tasks per chapter)
            base_idx = idx * 3
            exercise_result = all_results[base_idx]
            course_result = all_results[base_idx + 1]
            evaluation_result = all_results[base_idx + 2]

            # Validate and convert results
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
                    logger.error(f"[CHAPTER-{idx}] Invalid course: {course_result}")
                course = CourseOutput.model_validate(course_result)
            else:
                course = course_result

            if isinstance(evaluation_result, dict):
                evaluation = ExerciseOutput.model_validate(evaluation_result)
            else:
                evaluation = evaluation_result

            # Create Chapter object
            chapter_output = Chapter(
                id_chapter=id_chapter,
                title=chapter_title,
                course=course,
                exercice=exercice,
                evaluation=evaluation,
            )
            chapters.append(chapter_output)

    rebuild_time = time.time() - rebuild_start

    # Create and return DeepCourseOutput
    final_start = time.time()
    deepcourse_output = DeepCourseOutput(
        id=str(uuid4()), title=synthesis.title, chapters=chapters
    )
    final_time = time.time() - final_start

    total_time = time.time() - start_time

    # Minimal performance logging
    logger.info(
        f"\nPerformance Summary\n"
        f"{'=' * 60}\n"
        f"DeepCourse Complete - {num_chapters} chapters\n"
        f"{'-' * 60}\n"
        f"Total: {total_time:.2f}s\n"
        f"├─ Parallel execution: {execution_time:.2f}s ({num_chapters * 3} tasks)\n"
        f"├─ Reconstruction: {rebuild_time:.3f}s\n"
        f"└─ Finalization: {final_time:.3f}s\n"
        f"{'=' * 60}\n"
    )

    # Storage

    if user_id := get_user_id():
        try:
            # Create sessions and map IDs for each chapter
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
                    dict_session.append(chapter_sessions)
                except Exception as e:
                    logger.error(
                        f"Error creating sessions for chapter {chapter.id_chapter}: {e}"
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
            logger.error(f"Error storing deepcourse: {e}")
            raise

    # Import here to avoid circular imports
    from src.models import GenerativeToolOutput

    return GenerativeToolOutput(
        agent=agent, completed=completed, redirect_id=redirect_id
    )
