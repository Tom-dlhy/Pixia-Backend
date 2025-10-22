from src.config import gemini_settings
from src.models import Open, QCM, ExercisePlan, ExercicePlanItem, ExerciseOutput, ExerciseSynthesis
from src.prompts import SYSTEM_PROMPT_OPEN, SYSTEM_PROMPT_QCM, SYSTEM_PROMPT_PLANNER_EXERCISES
import logging, asyncio, uuid
from typing import Any, Union
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

def generate_plain(prompt: str, difficulty: str) -> Union[Open, dict, Any]:
    """Génère des questions à réponse ouverte basées sur la description de l'exercice fournie.

    Args:
        prompt (str): Description détaillée du sujet des exercices à générer.
        difficulty (str): Niveau de difficulté de l'exercice.

    Returns:
        dict: Dictionnaire représentant les questions générées.
    """

    prompt = f"Description: {prompt}\nDifficulté: {difficulty}"

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT_OPEN,
            "response_mime_type": "application/json",
            "response_schema": Open,
        },
    )
    logging.info(f"Response: {response}")
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
        logging.info(f"Réponse générée : {data}")

    except Exception as err:
        logging.error(f"Erreur parsing {err}")
        data = {}

    return data

def generate_qcm(prompt: str, difficulty: str) -> Union[QCM, dict, Any]:
    """Génère un QCM basé sur la description de l'exercice fournie.

    Args:
        prompt (str): Description détaillée du sujet des exercices à générer.
        difficulty (str): Niveau de difficulté de l'exercice.

    Returns:
        dict: Dictionnaire représentant le QCM généré.
    """

    prompt = f"Description: {prompt}\nDifficulté: {difficulty}"

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT_QCM,
            "response_mime_type": "application/json",
            "response_schema": QCM,
        },
    )
    logging.info(f"Response: {response}")
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
        logging.info(f"Réponse générée : {data}")

    except Exception as err:
        logging.error(f"Erreur parsing {err}")

    return data

def planner_exercises(synthesis: ExerciseSynthesis) -> Union[ExercisePlan, dict, Any]:
    """
    Génère un plan d'exercice basé sur la description, la difficulté, le nombre d'exercices et le type d'exercice.

    Args:
        description (str): Description détaillée du sujet des exercices à générer.
        difficulty (str): Niveau de difficulté de l'exercice.
        number_of_exercises (int): Nombre d'exercices à générer (entre 1 et 20).
        exercise_type (str): Type d'exercice à générer : qcm / open / both.

    Returns:
        dict: Dictionnaire contenant le plan d'exercice généré.

    """

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=f"Description: {synthesis.description}\nDifficulté: {synthesis.difficulty}\nNombre d'exercices: {synthesis.number_of_exercises}\nType d'exercice: {synthesis.exercise_type}",
        config={
            "system_instruction": SYSTEM_PROMPT_PLANNER_EXERCISES,
            "response_mime_type": "application/json",
            "response_schema": ExercisePlan,
        },
    )
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
    except Exception as err:
        logging.error(f"Erreur parsing {err}")
        data = {}

    return data

async def generate_for_topic(item: ExercicePlanItem, difficulty: str) -> Union[ExerciseOutput, dict, Any, None]:
    """Génère un exercice (QCM ou Open) pour un sujet donné."""
    try:
        if item.type == "qcm":
            logging.info(f"Génération du QCM : {item.topic}")
            result = await asyncio.to_thread(generate_qcm, item.topic, difficulty)
        else:
            logging.info(f"Génération du Open : {item.topic}")
            result = await asyncio.to_thread(generate_plain, item.topic, difficulty)
        return result
    except Exception as e:
        logging.error(f"Erreur lors de la génération de {item.topic} : {e}")
        return None

