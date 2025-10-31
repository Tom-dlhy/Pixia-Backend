"""Exercise generation tool with planning and parallel execution.

Generates exercises using a planning phase followed by parallel generation
with comprehensive error handling and retry logic.
"""

import asyncio
import logging
from typing import Union
from uuid import uuid4

from google.adk.sessions.database_session_service import DatabaseSessionService

from src.bdd import DBManager
from src.config import app_settings, database_settings
from src.models import (
    ExerciseOutput,
    ExercisePlan,
    ExerciseSynthesis,
    GenerativeToolOutput,
)
from src.utils import generate_for_topic, get_user_id, planner_exercises_async
from src.utils.timing import Timer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_exercises(
    is_called_by_agent: bool, synthesis: ExerciseSynthesis
) -> Union[GenerativeToolOutput, ExerciseOutput]:
    """Génère un exercice à partir d'un ExerciseSynthesis.

    Processus:
    1. Valider l'ExerciseSynthesis
    2. Appeler le planificateur d'exercices avec une logique de nouvelle tentative (max 3 tentatives avec un backoff exponentiel)
    3. Générer tous les exercices en parallèle en utilisant generate_for_topic
    4. Filtrer et valider les résultats
    5. Stocker dans la base de données si appelé par l'agent
    6. Retourner ExerciseOutput avec tous les exercices générés

    Args:
        is_called_by_agent: Si appelé par un agent (affecte le format de retour)
        synthesis: ExerciseSynthesis avec titre et paramètres de difficulté

    Returns:
        ExerciseOutput avec tous les exercices si non appelé par l'agent,
        GenerativeToolOutput si appelé par l'agent
    """
    db_session_service = DatabaseSessionService(
        db_url=database_settings.dsn,
    )
    bdd_manager = DBManager()

    agent = "exercise"
    redirect_id = None
    completed = False

    if isinstance(synthesis, dict):
        synthesis = ExerciseSynthesis.model_validate(synthesis)

    with Timer(f"Exercises: {synthesis.title}"):
        # Call exercise planner asynchronously with retry
        max_retries = 3
        retry_delay = 2  # seconds
        timeout_seconds = 60  # 60 second timeout per attempt (Gemini can be slow)
        plan_json = None

        for attempt in range(max_retries):
            try:
                with Timer(
                    f"├─ Planner (attempt {attempt + 1}/{max_retries})"
                ):
                    # Add timeout to prevent blocking
                    plan_json = await asyncio.wait_for(
                        planner_exercises_async(synthesis), timeout=timeout_seconds
                    )
                break  # Success, exit retry loop
            except asyncio.TimeoutError:
                logger.error(
                    f"Timeout after {timeout_seconds}s (attempt {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)
                    logger.info(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed after {max_retries} attempts (timeout)")
                    return GenerativeToolOutput(
                        agent=agent, redirect_id=redirect_id, completed=completed
                    )
            except Exception as err:
                logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {err}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2**attempt)  # Exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed after {max_retries} attempts")
                    return GenerativeToolOutput(
                        agent=agent, redirect_id=redirect_id, completed=completed
                    )

        # Final verification
        if plan_json is None:
            logger.error("plan_json is None after all retries")
            return GenerativeToolOutput(
                agent=agent, redirect_id=redirect_id, completed=completed
            )

        # Validate plan
        try:
            if isinstance(plan_json, ExercisePlan):
                plan = plan_json
            elif isinstance(plan_json, dict):
                plan = ExercisePlan.model_validate(plan_json)
            elif isinstance(plan_json, str):
                plan = ExercisePlan.model_validate_json(plan_json)
            else:
                raise TypeError("Unexpected output format.")

        except Exception as err:
            logger.error(f"Exercise plan validation error: {err}")
            return GenerativeToolOutput(
                agent=agent, redirect_id=redirect_id, completed=completed
            )

        # Create tasks for all exercises in plan
        tasks = [
            generate_for_topic(ex, synthesis.difficulty) for ex in plan.exercises
        ]

        # Parallel execution
        with Timer(f"├─ Generation ({len(tasks)} exercises)"):
            results = await asyncio.gather(*tasks)

        # Filter and convert valid results
        generated_exercises = []
        for idx, r in enumerate(results):
            if r is None:
                logger.warning(
                    f"Exercise {idx + 1}/{len(results)} is None, skipped"
                )
                continue

            # Ignore empty dictionaries
            if isinstance(r, dict):
                if not r or "type" not in r:
                    logger.warning(
                        f"Exercise {idx + 1}/{len(results)} is empty dict or missing 'type', skipped"
                    )
                    continue
                generated_exercises.append(r)
            elif hasattr(r, "model_dump"):
                generated_exercises.append(r.model_dump())
            else:
                generated_exercises.append(r)

        # Verify at least one valid exercise remains
        if not generated_exercises:
            logger.error(
                f"No valid exercises generated from {len(results)} attempts"
            )
            return GenerativeToolOutput(
                agent=agent, redirect_id=redirect_id, completed=False
            )

        logger.info(
            f"{len(generated_exercises)}/{len(results)} valid exercises generated"
        )

        exercise_output = ExerciseOutput(
            id=str(uuid4()), exercises=generated_exercises, title=synthesis.title
        )

        # Storage

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
                agent=agent, redirect_id=redirect_id, completed=completed
            )

        else:
            return exercise_output
