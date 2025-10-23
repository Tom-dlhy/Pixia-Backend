import asyncio
import logging
from uuid import uuid4

from src.models import (
    Chapter,
    ChapterSynthesis,
    CourseOutput,
    DeepCourseSynthesis,
    ExerciseOutput,
)
from src.tools.exercises_tools import generate_exercises
from src.tools.cours_tools import generate_courses
from src.config import gemini_settings
from src.prompts import SYSTEM_PROMPT_GENERATE_NEW_CHAPTER

logging.basicConfig(level=logging.INFO)


async def generate_new_chapter(deepcourse_synthesis: DeepCourseSynthesis | dict,) -> Chapter:
    """Generate a Chapter from a DeepCourse synthesis description."""
    
    if isinstance(deepcourse_synthesis, dict):
        deepcourse_synthesis = DeepCourseSynthesis.model_validate(
            deepcourse_synthesis
        )

    lines = [f"Titre du Deepcourse : {deepcourse_synthesis.title}", ""]
    for idx, chapter in enumerate(deepcourse_synthesis.synthesis_chapters, start=1):
        lines.append(f"Titre du chapitre numero {idx} : {chapter.chapter_title}")
        lines.append(
            f"\tDescription du chapitre numero {idx} : {chapter.chapter_description}"
        )
    text = "\n".join(lines)

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=SYSTEM_PROMPT_GENERATE_NEW_CHAPTER + "\n" + text,
        config={
            "response_mime_type": "application/json",
            "response_schema": ChapterSynthesis,
        },
    )

    try:
        if hasattr(response, "parsed") and response.parsed:
            synthesis_chapter = response.parsed
        else:
            payload = getattr(response, "text", None)
            if isinstance(payload, str):
                synthesis_chapter = ChapterSynthesis.model_validate_json(payload)
            else:
                synthesis_chapter = ChapterSynthesis.model_validate(payload)
        logging.info("Reponse generee : %s", synthesis_chapter)
    except Exception as err:
        logging.error("Erreur parsing %s", err)
        raise

    exercise_result, course_result, evaluation_result = await asyncio.gather(
        generate_exercises(synthesis_chapter.synthesis_exercise),
        generate_courses(synthesis_chapter.synthesis_course),
        generate_exercises(synthesis_chapter.synthesis_evaluation),
    )

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

    return Chapter(
        id_chapter=str(uuid4()),
        title=synthesis_chapter.chapter_title,
        course=course,
        exercice=exercice,
        evaluation=evaluation,
    )
