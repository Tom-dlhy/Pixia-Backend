import logging
from src.models.cours_models import CourseSynthesis, CoursePlan, CoursOutput
from src.utils import planner_cours, generate_for_chapter
import json
import asyncio
import uuid

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
    tasks = [generate_for_chapter(chapter, course_synthesis.difficulty) for chapter in plan.chapters]

    # Exécution en parallèle
    results = await asyncio.gather(*tasks)

    # Filtrage des résultats valides
    generated_cours = [r for r in results if r is not None]

    logging.info(f"{len(generated_cours)} cours générés avec succès.")
    # Convertir la liste de cours générés en un vrai CoursOutput

    cours_output = CoursOutput(title=plan.title, chapters=generated_cours)

    # Ajouter de l'id du cours_output
    # Si l'objet a un champ 'id' et qu'il est vide → on le remplit
    if hasattr(cours_output, "id") and getattr(cours_output, "id") in (None, ""):
        setattr(cours_output, "id", str(uuid.uuid4()))


    return cours_output.model_dump()
