import asyncio
from src.models import (
    DeepCourseSynthesis,
    DeepCourseOutput,
    Chapter,
    ExerciseOutput,
    CourseOutput,
)
from src.tools.exercises_tools import generate_exercises
from src.tools.cours_tools import generate_courses
from src.utils.timing import Timer
from src.utils import get_user_id
from uuid import uuid4
import json
import logging
import time

from src.config import database_settings, app_settings
from google.adk.sessions.database_session_service import DatabaseSessionService
from src.bdd import DBManager
from src.models import GenerativeToolOutput
from uuid import uuid4

from typing import List, Dict

logger = logging.getLogger(__name__)


async def generate_deepcourse(synthesis: dict) -> GenerativeToolOutput:
    """
    Génère un deepcourse complet avec tous ses chapitres, exercices et évaluations.

    Args:
        synthesis: Objet DeepCourseSynthesis contenant:
            - title: Titre du deepcourse
            - synthesis_chapters: Liste des chapitres (1-16) avec structure complète

    Returns:
        GenerativeToolOutput avec agent, completed, redirect_id

    Utilisation:
        Appelle ce tool une fois que l'utilisateur a validé le plan du deepcourse.
        Le tool génère en parallèle tous les cours, exercices et évaluations.
    """

    logger.info("🚀 [GENERATE_DEEPCOURSE] Tool appelé!")

    if isinstance(synthesis, dict):
        logger.info(f"   Conversion dict → DeepCourseSynthesis...")
        synthesis = DeepCourseSynthesis.model_validate(synthesis)
        logger.info("✅ DeepCourseSynthesis validée depuis dict")

    logger.info(f"   Titre: {synthesis.title}")
    logger.info(f"   Chapitres: {len(synthesis.synthesis_chapters)}")

    db_session_service = DatabaseSessionService(
        db_url=database_settings.dsn,
    )
    bdd_manager = DBManager()

    agent = "deep-course"
    redirect_id = None
    completed = False

    start_time = time.time()

    synthesis_chapters = synthesis.synthesis_chapters
    num_chapters = len(synthesis_chapters)

    task_creation_start = time.time()
    all_tasks = []
    task_descriptions = []

    for idx, chapter in enumerate(synthesis_chapters):
        logger.info(f"📋 Chapitre {idx+1}: {chapter.chapter_title}")

        logger.info(f"   ├─ Exercices: {chapter.synthesis_exercise.title}")
        all_tasks.append(
            generate_exercises(
                is_called_by_agent=False, synthesis=chapter.synthesis_exercise
            )
        )
        task_descriptions.append(f"CH{idx+1}-Exercices")

        logger.info(f"   ├─ Cours")
        all_tasks.append(
            generate_courses(
                is_called_by_agent=False, course_synthesis=chapter.synthesis_course
            )
        )
        task_descriptions.append(f"CH{idx+1}-Cours")

        logger.info(f"   └─ Évaluation: {chapter.synthesis_evaluation.title}")
        all_tasks.append(
            generate_exercises(
                is_called_by_agent=False, synthesis=chapter.synthesis_evaluation
            )
        )
        task_descriptions.append(f"CH{idx+1}-Evaluation")

    task_creation_time = time.time() - task_creation_start
    logger.info(f"⏱️  {len(all_tasks)} tâches créées en {task_creation_time:.2f}s")

    logger.info(f"🔄 Lancement de l'exécution parallèle...")
    logger.info(f"   ⏱️  Timeout par tâche: 180s (3 min)")
    logger.info(f"   📦 Total tâches: {len(all_tasks)}")
    
    execution_start = time.time()
    try:
        # Utiliser asyncio.wait_for pour timeout global sur toutes les tâches
        # Timeout = 60s par tâche * nb_chapters * 3 + buffer
        timeout_per_task = 180  # 3 min par tâche (exercice/cours/evaluation)
        total_timeout = timeout_per_task * num_chapters + 60  # +60s de buffer
        logger.info(f"   ⏰ Timeout global: {total_timeout}s pour {num_chapters} chapitre(s)")
        
        all_results = await asyncio.wait_for(
            asyncio.gather(*all_tasks, return_exceptions=False),
            timeout=total_timeout
        )
        logger.info(f"✅ Toutes les tâches complétées avec succès")
    except asyncio.TimeoutError as te:
        logger.error(
            f"❌ TIMEOUT lors de l'exécution parallèle après {total_timeout}s"
        )
        logger.error(f"   Tâches complétées: {num_chapters * 3} attendues")
        logger.error(f"   Cette erreur survient généralement avec:")
        logger.error(f"   - Deepcourses très larges (>8 chapitres)")
        logger.error(f"   - Contenu très détaillé (level_detail=detailed)")
        logger.error(f"   - Rate limiting Gemini API")
        raise RuntimeError(
            f"Timeout deepcourse: {num_chapters} chapitres trop lourds ou API rate-limitée"
        )
    except Exception as e:
        logger.error(f"❌ ERREUR lors de l'exécution parallèle: {e}")
        logger.error(f"   Type d'erreur: {type(e).__name__}")
        logger.error(f"   Cela peut indiquer un problème de credentials ou API limit")
        raise

    execution_time = time.time() - execution_start
    logger.info(
        f"⏱️  Exécution parallèle: {execution_time:.2f}s ({num_chapters * 3} tâches)"
    )

    # Reconstruire les résultats par chapitre
    rebuild_start = time.time()
    chapters = []
    for idx, chapter_synthesis in enumerate(synthesis_chapters):
        with Timer(f"[CH-{idx+1}] Reconstruction"):
            id_chapter = str(uuid4())
            chapter_title = chapter_synthesis.chapter_title

            # Récupérer les résultats pour ce chapitre (3 tasks par chapitre)
            base_idx = idx * 3
            exercise_result = all_results[base_idx]
            course_result = all_results[base_idx + 1]
            evaluation_result = all_results[base_idx + 2]

            # Valider et convertir les résultats
            if isinstance(exercise_result, dict):
                exercice = ExerciseOutput.model_validate(exercise_result)
            else:
                exercice = exercise_result

            if isinstance(course_result, dict):
                if (
                    not course_result
                    or "title" not in course_result
                    or "parts" not in course_result
                ):
                    logger.error(f"[CHAPTER-{idx}] Cours invalide: {course_result}")
                course = CourseOutput.model_validate(course_result)
            else:
                course = course_result

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
                evaluation=evaluation,
            )
            chapters.append(chapter_output)

    rebuild_time = time.time() - rebuild_start

    # Créer et retourner le DeepCourseOutput
    final_start = time.time()
    deepcourse_output = DeepCourseOutput(
        id=str(uuid4()), title=synthesis.title, chapters=chapters
    )
    final_time = time.time() - final_start

    total_time = time.time() - start_time

    # Log minimaliste de performance
    logger.info(f"\n📊 ╔═══════════════════════════════════════════════════════════╗")
    logger.info(f"  ║  DEEPCOURSE COMPLÈTE - {num_chapters} chapitres")
    logger.info(f"  ╠═══════════════════════════════════════════════════════════╣")
    logger.info(f"  ║  ⏱️  Total: {total_time:.2f}s")
    logger.info(
        f"  ║     └─ Exécution parallèle: {execution_time:.2f}s ({num_chapters * 3} tâches)"
    )
    logger.info(f"  ║     └─ Reconstruction: {rebuild_time:.3f}s")
    logger.info(f"  ║     └─ Finalisation: {final_time:.3f}s")
    logger.info(f"  ╚═══════════════════════════════════════════════════════════╝\n")

    ### Storage

    if user_id := get_user_id():

        try:
            # Créer les sessions et mapper les IDs pour chaque chapitre
            dict_session: List[Dict[str, str]] = []

            for chapter in deepcourse_output.chapters:
                try:
                    session_exercise = await db_session_service.create_session(
                        app_name=app_settings.APP_NAME,
                        user_id=user_id,
                    )
                    session_course = await db_session_service.create_session(
                        app_name=app_settings.APP_NAME,
                        user_id=user_id,
                    )
                    session_evaluation = await db_session_service.create_session(
                        app_name=app_settings.APP_NAME,
                        user_id=user_id,
                    )

                    chapter_sessions = {
                        "id_chapter": chapter.id_chapter,
                        "session_id_exercise": session_exercise.id,
                        "session_id_course": session_course.id,
                        "session_id_evaluation": session_evaluation.id,
                    }
                    dict_session.append(chapter_sessions)
                except Exception as e:
                    logger.error(
                        f"❌ Erreur lors de la création des sessions pour le chapitre {chapter.id_chapter}: {e}"
                    )
                    raise

            await bdd_manager.store_deepcourse(
                user_id=user_id,
                content=deepcourse_output,
                dict_session=dict_session,
            )
            redirect_id = deepcourse_output.id
            completed = True
        except Exception as e:
            logger.error(f"❌ Erreur lors du stockage du deepcourse: {e}")
            raise

    return GenerativeToolOutput(
        agent=agent, completed=completed, redirect_id=redirect_id
    )
