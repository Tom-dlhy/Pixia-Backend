import asyncio
from src.models import DeepCourseSynthesis, DeepCourseOutput, Chapter, ExerciseOutput, CourseOutput
from src.tools.exercises_tools import generate_exercises
from src.tools.cours_tools import generate_courses
from uuid import uuid4
import json

async def generate_deepcourse(synthesis: DeepCourseSynthesis) -> DeepCourseOutput:
    if isinstance(synthesis, dict):
        synthesis = DeepCourseSynthesis(**synthesis)
    
    synthesis_chapters = synthesis.synthesis_chapters

    tasks = [
        asyncio.gather(
            generate_exercises(chapter.synthesis_exercise),
            generate_courses(chapter.synthesis_course),
            generate_exercises(chapter.synthesis_evaluation)
        )
        for chapter in synthesis_chapters
    ]
    
    results = await asyncio.gather(*tasks)
    chapters = []
    
    for idx, chapitre in enumerate(results):
        id_chapter = str(uuid4())
        chapter_title = synthesis_chapters[idx].chapter_title
        
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
    print(json.dumps(deepcourse_output.model_dump(), indent=2, ensure_ascii=False))
    return deepcourse_output