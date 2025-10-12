from src.utils import planner, generate_for_topic, assign_uuids_to_output
from src.models import ExercisePlan, ExerciseOutput, ExerciseSynthesis
from typing import Union
import asyncio, logging, json

logging.basicConfig(level=logging.INFO)

async def generate_exercises(synthesis: ExerciseSynthesis) -> ExerciseOutput:
    plan_json = planner(synthesis.description, synthesis.difficulty, synthesis.number_of_exercises, synthesis.exercise_type)

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

    return assign_uuids_to_output(generated_exercises)