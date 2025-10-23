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
from uuid import uuid4
import json
import logging
import time

logger = logging.getLogger(__name__)


async def generate_deepcourse(synthesis: DeepCourseSynthesis) -> DeepCourseOutput:
    start_time = time.time()
    if isinstance(synthesis, dict):
        synthesis = DeepCourseSynthesis(**synthesis)

    synthesis_chapters = synthesis.synthesis_chapters
    num_chapters = len(synthesis_chapters)

    # Créer TOUS les tasks en parallèle
    task_creation_start = time.time()
    all_tasks = []
    for chapter in synthesis_chapters:
        # Créer les coroutines SANS les attendre
        all_tasks.append(generate_exercises(chapter.synthesis_exercise))
        all_tasks.append(generate_courses(chapter.synthesis_course))
        all_tasks.append(generate_exercises(chapter.synthesis_evaluation))
    task_creation_time = time.time() - task_creation_start

    # Exécuter TOUS les tasks en parallèle
    execution_start = time.time()
    all_results = await asyncio.gather(*all_tasks)
    execution_time = time.time() - execution_start

    # Reconstruire les résultats par chapitre
    rebuild_start = time.time()
    chapters = []
    for idx, chapter_synthesis in enumerate(synthesis_chapters):
        with Timer(f"[CH-{idx+1}] Reconstruction"):
            id_chapter = str(uuid4())
            chapter_title = chapter_synthesis.chapter_title

            # Récupérer les résultats pour ce chapitre (3 tasks par chapitre)
            base_idx = idx * 3
            exercise_result = all_results[base_idx]
            course_result = all_results[base_idx + 1]
            evaluation_result = all_results[base_idx + 2]

            # Valider et convertir les résultats
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

            # Créer l'objet Chapter
            chapter_output = Chapter(
                id_chapter=id_chapter,
                title=chapter_title,
                course=course,
                exercice=exercice,
                evaluation=evaluation,
            )
            chapters.append(chapter_output)

    rebuild_time = time.time() - rebuild_start

    # Créer et retourner le DeepCourseOutput
    final_start = time.time()
    deepcourse_output = DeepCourseOutput(
        id=str(uuid4()), title=synthesis.title, chapters=chapters
    )
    final_time = time.time() - final_start

    total_time = time.time() - start_time

    # Log minimaliste de performance
    logger.info(f"\n📊 ╔═══════════════════════════════════════════════════════════╗")
    logger.info(f"  ║  DEEPCOURSE COMPLÈTE - {num_chapters} chapitres")
    logger.info(f"  ╠═══════════════════════════════════════════════════════════╣")
    logger.info(f"  ║  ⏱️  Total: {total_time:.2f}s")
    logger.info(
        f"  ║     └─ Exécution parallèle: {execution_time:.2f}s ({num_chapters * 3} tâches)"
    )
    logger.info(f"  ║     └─ Reconstruction: {rebuild_time:.3f}s")
    logger.info(f"  ║     └─ Finalisation: {final_time:.3f}s")
    logger.info(f"  ╚═══════════════════════════════════════════════════════════╝\n")

    return deepcourse_output
