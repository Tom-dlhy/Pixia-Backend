import asyncio
import json
import logging

from src.models.exercise_models import ExercisePlan, ExerciseOutput, ExerciseSynthesis
from src.utils import assign_uuids_to_output, generate_for_topic, planner_exercises


logging.basicConfig(level=logging.INFO)


async def generate_exercises(synthesis: ExerciseSynthesis) -> dict:
    if isinstance(synthesis, dict):
        synthesis = ExerciseSynthesis(**synthesis)
    plan_json = planner_exercises(synthesis)

    # Validation du plan
    try:
        if isinstance(plan_json, ExercisePlan):
            plan = plan_json
        elif isinstance(plan_json, dict):
            plan = ExercisePlan.model_validate(plan_json)
        elif isinstance(plan_json, str):
            plan = ExercisePlan.model_validate_json(plan_json)
        else:
            raise TypeError("Format de sortie inattendu.")

        print(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False))
    except Exception as err:
        logging.error(f"Erreur de validation du plan d'exercice: {err}")
        return plan_json

    # Création des tâches pour tous les exercices du plan
    tasks = [generate_for_topic(ex, synthesis.difficulty) for ex in plan.exercises]

    # Exécution en parallèle
    results = await asyncio.gather(*tasks)

    # Filtrage des résultats valides
    generated_exercises = [r for r in results if r is not None]

    logging.info(f"{len(generated_exercises)} exercices générés avec succès.")
    # Convertir la liste d'exercices générés en un vrai ExerciseOutput

    exercise_output = ExerciseOutput(exercises=generated_exercises)
    assign_uuids_to_output(exercise_output)

    return exercise_output.model_dump()
