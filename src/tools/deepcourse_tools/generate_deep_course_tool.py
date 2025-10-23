import asyncio
from src.models import DeepCourseSynthesis, DeepCourseOutput, Chapter, ExerciseOutput, CourseOutput
from src.tools.exercises_tools import generate_exercises
from src.tools.cours_tools import generate_courses
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
    logger.info(f"🚀 Génération d'un deepcourse avec {len(synthesis_chapters)} chapitres en parallèle")

    # Créer TOUS les tasks en parallèle (pas par chapitre)
    all_tasks = []
    for chapter in synthesis_chapters:
        all_tasks.append(generate_exercises(chapter.synthesis_exercise))
        all_tasks.append(generate_courses(chapter.synthesis_course))
        all_tasks.append(generate_exercises(chapter.synthesis_evaluation))
    
    logger.info(f"⏳ Exécution de {len(all_tasks)} tâches en parallèle (3 par chapitre)")
    
    # Exécuter TOUS les tasks en parallèle
    all_results = await asyncio.gather(*all_tasks)
    
    # Reconstruire les résultats par chapitre
    chapters = []
    for idx, chapter_synthesis in enumerate(synthesis_chapters):
        id_chapter = str(uuid4())
        chapter_title = chapter_synthesis.chapter_title
        
        # Récupérer les résultats pour ce chapitre (3 tasks par chapitre)
        base_idx = idx * 3
        exercise_result = all_results[base_idx]
        course_result = all_results[base_idx + 1]
        evaluation_result = all_results[base_idx + 2]
        
        logger.debug(f"✓ Chapitre {idx + 1}/{len(synthesis_chapters)}: {chapter_title}")
        
        # Valider et convertir les résultats
        if isinstance(exercise_result, dict):
            exercice = ExerciseOutput.model_validate(exercise_result)
        else:
            exercice = exercise_result
            
        if isinstance(course_result, dict):
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
            evaluation=evaluation
        )
        chapters.append(chapter_output)

    # Créer et retourner le DeepCourseOutput
    deepcourse_output = DeepCourseOutput(
        id=str(uuid4()),
        title=synthesis.title,
        chapters=chapters
    )
    
    logger.info(f"✅ DeepCourse généré avec succès: {deepcourse_output.title}")
    logger.info(f"⏱️ Temps total de génération: {time.time() - start_time:.2f} secondes")
    return deepcourse_output