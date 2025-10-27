import asyncio
import logging
from uuid import uuid4
from typing import Union

from src.models import ExercisePlan, ExerciseOutput, ExerciseSynthesis, GenerativeToolOutput
from src.utils import generate_for_topic, planner_exercises_async, get_user_id
from src.utils.timing import Timer

from src.config import database_settings, app_settings
from google.adk.sessions.database_session_service import DatabaseSessionService
from src.bdd import DBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




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

    with Timer(f"Exercices: {synthesis.title}"):
        # Appeler le planner de manière async avec retry
        max_retries = 3
        retry_delay = 2  # secondes
        timeout_seconds = 30  # Timeout de 30 secondes par tentative
        plan_json = None
        
        for attempt in range(max_retries):
            try:
                with Timer(f"  └─ Planner (tentative {attempt + 1}/{max_retries})"):
                    # Ajouter un timeout pour éviter les blocages
                    plan_json = await asyncio.wait_for(
                        planner_exercises_async(synthesis),
                        timeout=timeout_seconds
                    )
                break  # Succès, sortir de la boucle
            except asyncio.TimeoutError:
                logger.error(f"⏱️ Timeout après {timeout_seconds}s (tentative {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.info(f"⏳ Attente de {wait_time}s avant retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Échec après {max_retries} tentatives (timeout)")
                    return GenerativeToolOutput(agent=agent, redirect_id=redirect_id, completed=completed)
            except Exception as err:
                logger.error(f"❌ Tentative {attempt + 1}/{max_retries} échouée: {err}")
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"⏳ Attente de {wait_time}s avant retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ Échec après {max_retries} tentatives")
                    return GenerativeToolOutput(agent=agent, redirect_id=redirect_id, completed=completed)

        # Vérification finale
        if plan_json is None:
            logger.error("❌ plan_json est None après tous les retries")
            return GenerativeToolOutput(agent=agent, redirect_id=redirect_id, completed=completed)

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

        except Exception as err:
            logger.error(f"Erreur de validation du plan d'exercice: {err}")
            return GenerativeToolOutput(agent=agent, redirect_id=redirect_id, completed=completed)

        # Création des tâches pour tous les exercices du plan
        tasks = [generate_for_topic(ex, synthesis.difficulty) for ex in plan.exercises]

        # Exécution en parallèle
        with Timer(f"  └─ Génération ({len(tasks)} exercices)"):
            results = await asyncio.gather(*tasks)

        # Filtrage et conversion des résultats valides
        generated_exercises = []
        for idx, r in enumerate(results):
            if r is None:
                logger.warning(f"⚠️ Exercice {idx + 1}/{len(results)} est None, ignoré")
                continue
            
            # Ignorer les dictionnaires vides
            if isinstance(r, dict):
                if not r or 'type' not in r:
                    logger.warning(f"⚠️ Exercice {idx + 1}/{len(results)} est un dict vide ou sans 'type', ignoré")
                    continue
                generated_exercises.append(r)
            elif hasattr(r, "model_dump"):
                generated_exercises.append(r.model_dump())
            else:
                generated_exercises.append(r)
        
        # Vérifier qu'il reste au moins un exercice valide
        if not generated_exercises:
            logger.error(f"❌ Aucun exercice valide généré sur {len(results)} tentatives")
            return GenerativeToolOutput(agent=agent, redirect_id=redirect_id, completed=False)
        
        logger.info(f"✅ {len(generated_exercises)}/{len(results)} exercices valides générés")

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
