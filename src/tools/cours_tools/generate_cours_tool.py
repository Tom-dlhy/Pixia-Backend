import logging
from src.models.cours_models import CourseSynthesis, CoursePlan, CourseOutput
from src.utils import planner_cours, generate_for_part
import json
import asyncio
import uuid

from src.utils.cours_utils import assign_uuids_to_output_course

logging.basicConfig(level=logging.INFO)


async def generate_courses(course_synthesis: CourseSynthesis) -> dict:
    if isinstance(course_synthesis, dict):
        course_synthesis = CourseSynthesis(**course_synthesis)
    plan_json = planner_cours(course_synthesis)

    # Validation du plan
    try:
        if isinstance(plan_json, CoursePlan):
            plan = plan_json
        elif isinstance(plan_json, dict):
            plan = CoursePlan.model_validate(plan_json)
        elif isinstance(plan_json, str):
            plan = CoursePlan.model_validate_json(plan_json)
        else:
            raise TypeError("Format de sortie inattendu.")

        print(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False))
    except Exception as err:
        logging.error(f"Erreur de validation du plan d'exercice: {err}")
        return plan_json

    # Création des tâches pour tous les exercices du plan
    tasks = [
        generate_for_part(part, course_synthesis.difficulty)
        for part in plan.parts
    ]

    # Ré-exécuter les parties en batch de 4 en parallèle
    results = []
    batch_size = 4
    for i in range(0, len(plan.parts), batch_size):
        batch = plan.parts[i : i + batch_size]
        batch_tasks = [
            generate_for_part(ch, course_synthesis.difficulty) for ch in batch
        ]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)

    # Filtrage des résultats valides
    generated_cours = [r for r in results if r is not None]

    logging.info(f"{len(generated_cours)} cours générés avec succès.")
    
    # Convertir la liste de cours générés en un vrai CourseOutput
    cours_output = CourseOutput(title=plan.title, parts=generated_cours)

    assign_uuids_to_output_course(cours_output)

    return cours_output.model_dump()
