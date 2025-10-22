import asyncio
import json
import logging
from uuid import uuid4
from typing import Any, Union

from src.models.exercise_models import ExercisePlan, ExerciseOutput, ExerciseSynthesis
from src.utils import generate_for_topic, planner_exercises


logging.basicConfig(level=logging.INFO)


async def generate_exercises(synthesis: ExerciseSynthesis) -> Union[dict, Any]:
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
        return plan_json if isinstance(plan_json, dict) else {}

    # Création des tâches pour tous les exercices du plan
    tasks = [generate_for_topic(ex, synthesis.difficulty) for ex in plan.exercises]

    # Exécution en parallèle
    results = await asyncio.gather(*tasks)

    # Filtrage et conversion des résultats valides
    generated_exercises = []
    for r in results:
        if r is not None:
            # Convertir en dict si nécessaire pour la validation
            if isinstance(r, dict):
                generated_exercises.append(r)
            elif hasattr(r, 'model_dump'):
                generated_exercises.append(r.model_dump())
            else:
                generated_exercises.append(r)

    logging.info(f"{len(generated_exercises)} exercices générés avec succès.")
    # Convertir la liste d'exercices générés en un vrai ExerciseOutput

    exercise_output = ExerciseOutput(id=str(uuid4()), exercises=generated_exercises)

    return exercise_output.model_dump()
