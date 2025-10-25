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
    if isinstance(synthesis, dict):
        synthesis = DeepCourseSynthesis(**synthesis)

    synthesis_chapters = synthesis.synthesis_chapters

    all_tasks = []
    for chapter in synthesis_chapters:
        all_tasks.append(generate_exercises(chapter.synthesis_exercise))
        all_tasks.append(generate_courses(chapter.synthesis_course))
        all_tasks.append(generate_exercises(chapter.synthesis_evaluation))

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
    return deepcourse_output
