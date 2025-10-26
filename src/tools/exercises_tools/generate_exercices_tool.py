import asyncio
import logging
from uuid import uuid4
from typing import Any, Union

from src.models.exercise_models import ExercisePlan, ExerciseOutput, ExerciseSynthesis
from src.utils import generate_for_topic, planner_exercises_async, get_user_id
from src.utils.timing import Timer

from src.config import database_settings, app_settings
from google.adk.sessions.database_session_service import DatabaseSessionService
from src.bdd import DBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.models import GenerativeToolOutput


async def generate_exercises(is_called_by_agent:bool ,synthesis: ExerciseSynthesis) -> Union[GenerativeToolOutput, ExerciseOutput]:
    
    db_session_service = DatabaseSessionService(
        db_url=database_settings.dsn,
    )
    bdd_manager = DBManager()

    agent = "exercise"
    redirect_id = None
    completed = False

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
            return GenerativeToolOutput(agent=agent, redirect_id=redirect_id, completed=completed)

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

        ### Storage


        if is_called_by_agent:

            if user_id := get_user_id():
                copilote_session_id = str(uuid4())
                await db_session_service.create_session(
                    session_id=copilote_session_id,
                    app_name=app_settings.APP_NAME,
                    user_id=user_id,
                )
                
                if isinstance(exercise_output, ExerciseOutput):
                    await bdd_manager.store_basic_document(
                        content=exercise_output,
                        session_id=copilote_session_id,
                        sub=user_id,
                    )
                
                    redirect_id = copilote_session_id
                    completed = bool(generated_exercises)

            return GenerativeToolOutput(
                agent=agent,
                redirect_id=redirect_id,
                completed=completed
            )

        else:
            return exercise_output
