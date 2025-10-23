import asyncio
from src.models import DeepCourseSynthesis, DeepCourseOutput, Chapter, ExerciseOutput, CourseOutput, ChapterSynthesis
from src.tools.exercises_tools import generate_exercises
from src.tools.cours_tools import generate_courses
from uuid import uuid4
import json
from google.genai import types
from src.config import gemini_settings
from src.prompts import SYSTEM_PROMPT_GENERATE_NEW_CHAPTER
import logging

logging.basicConfig(level=logging.INFO)

async def generate_new_chapter(deepcourse_synthesis:DeepCourseSynthesis) -> Chapter :

    text="Titre du Deepcourse : {deepcourse_synthesis.title}\n\n"
    i=0
    for chapter in deepcourse_synthesis.synthesis_chapters:
        i+=1
        text+="Titre du chapitre numéro {i} :"+chapter.chapter_title+"\n"+"\t"+"Description du chapitre numéro {i} : "+chapter.chapter_description + "\n"
    
    response = gemini_settings.CLIENT.models.generate_content(
            model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
            contents=SYSTEM_PROMPT_GENERATE_NEW_CHAPTER + "\n" + text,
            config={
            "response_mime_type": "application/json",
            "response_schema": ChapterSynthesis,
        },
        )
    
    try:
        synthesis_chapter = response.parsed if hasattr(response, "parsed") else response.text
        logging.info(f"Réponse générée : {synthesis_chapter}")

    except Exception as err:
        logging.error(f"Erreur parsing {err}")
    
    tasks = [
        asyncio.gather(
            generate_exercises(synthesis_chapter.synthesis_exercise),
            generate_courses(synthesis_chapter.synthesis_course),
            generate_exercises(synthesis_chapter.synthesis_evaluation)
        )
        for chapter in synthesis_chapter
    ]
    
    results = await asyncio.gather(*tasks)
    chapters = []
    
    for idx, chapitre in enumerate(results):
        id_chapter = str(uuid4())
        chapter_title = synthesis_chapter[idx].chapter_title
        
        # Récupérer et valider les objets
        exercise_result = chapitre[0]
        if isinstance(exercise_result, dict):
            exercice = ExerciseOutput.model_validate(exercise_result)
        else:
            exercice = exercise_result
            
        course_result = chapitre[1]
        if isinstance(course_result, dict):
            course = CourseOutput.model_validate(course_result)
        else:
            course = course_result
            
        evaluation_result = chapitre[2]
        if isinstance(evaluation_result, dict):
            evaluation = ExerciseOutput.model_validate(evaluation_result)
        else:
            evaluation = evaluation_result
        
        chapter_output = Chapter(
            id_chapter=id_chapter,
            title=chapter_title,
            course=course,
            exercice=exercice,
            evaluation=evaluation
        )
        
    return chapter_output