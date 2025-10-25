import asyncio
import logging
from uuid import uuid4
from typing import Any, Union

from src.models.exercise_models import ExercisePlan, ExerciseOutput, ExerciseSynthesis
from src.utils import generate_for_topic
from src.utils import planner_exercises_async
from src.utils.timing import Timer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_exercises(synthesis: ExerciseSynthesis) -> Union[dict, Any]:
    if isinstance(synthesis, dict):
        synthesis = ExerciseSynthesis(**synthesis)
        plan_json = await planner_exercises_async(synthesis)

        try:
            if isinstance(plan_json, ExercisePlan):
                plan = plan_json
            elif isinstance(plan_json, dict):
                plan = ExercisePlan.model_validate(plan_json)
            elif isinstance(plan_json, str):
                plan = ExercisePlan.model_validate_json(plan_json)
            else:
                raise TypeError("Format de sortie inattendu.")

        except Exception as err:
            logger.error(f"Erreur de validation du plan d'exercice: {err}")
            return plan_json if isinstance(plan_json, dict) else {}

        tasks = [generate_for_topic(ex, synthesis.difficulty) for ex in plan.exercises]

        
        results = await asyncio.gather(*tasks)

        generated_exercises = []
        for r in results:
            if r is not None:
                if isinstance(r, dict):
                    generated_exercises.append(r)
                elif hasattr(r, "model_dump"):
                    generated_exercises.append(r.model_dump())
                else:
                    generated_exercises.append(r)

        exercise_output = ExerciseOutput(
            id=str(uuid4()), exercises=generated_exercises, title=synthesis.title
        )

        return exercise_output.model_dump()
