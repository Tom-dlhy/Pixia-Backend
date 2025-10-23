from src.config import gemini_settings
from src.models import (
    Open,
    QCM,
    ExercisePlan,
    ExercicePlanItem,
    ExerciseOutput,
    ExerciseSynthesis,
)
from src.prompts import (
    SYSTEM_PROMPT_OPEN,
    SYSTEM_PROMPT_QCM,
    SYSTEM_PROMPT_PLANNER_EXERCISES,
)
import logging, asyncio, uuid
from typing import Any, Union
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)


async def generate_plain(prompt: str, difficulty: str) -> Union[Open, dict, Any]:
    """Génère des questions à réponse ouverte basées sur la description de l'exercice fournie.

    Args:
        prompt (str): Description détaillée du sujet des exercices à générer.
        difficulty (str): Niveau de difficulté de l'exercice.

    Returns:
        dict: Dictionnaire représentant les questions générées.
    """

    prompt = f"Description: {prompt}\nDifficulté: {difficulty}"

    response = await gemini_settings.CLIENT.aio.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT_OPEN,
            "response_mime_type": "application/json",
            "response_schema": Open,
        },
    )
    try:
        data = response.parsed
    except Exception as err:
        logging.error(f"Erreur parsing {err}")
        data = {}

    return data


async def generate_qcm(prompt: str, difficulty: str) -> Union[QCM, dict, Any]:
    """Génère un QCM basé sur la description de l'exercice fournie.

    Args:
        prompt (str): Description détaillée du sujet des exercices à générer.
        difficulty (str): Niveau de difficulté de l'exercice.

    Returns:
        dict: Dictionnaire représentant le QCM généré.
    """

    prompt = f"Description: {prompt}\nDifficulté: {difficulty}"

    response = await gemini_settings.CLIENT.aio.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT_QCM,
            "response_mime_type": "application/json",
            "response_schema": QCM,
        },
    )
    try:
        data = response.parsed
    except Exception as err:
        logging.error(f"Erreur parsing {err}")
        data = {}

    return data

async def planner_exercises_async(
    synthesis: ExerciseSynthesis,
) -> Union[ExercisePlan, dict, Any]:
    """
    Version async de planner_exercises - utilise le client async de Google.

    Génère un plan d'exercice de manière asynchrone sans bloquer le thread.
    """

    response = await gemini_settings.CLIENT.aio.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=f"Description: {synthesis.description}\nDifficulté: {synthesis.difficulty}\nNombre d'exercices: {synthesis.number_of_exercises}\nType d'exercice: {synthesis.exercise_type}",
        config={
            "system_instruction": SYSTEM_PROMPT_PLANNER_EXERCISES,
            "response_mime_type": "application/json",
            "response_schema": ExercisePlan,
        },
    )
    try:
        data = response.parsed
    except Exception as err:
        logging.error(f"Erreur parsing {err}")
        data = {}

    return data


async def generate_for_topic(
    item: ExercicePlanItem, difficulty: str
) -> Union[ExerciseOutput, dict, Any, None]:
    """Génère un exercice (QCM ou Open) pour un sujet donné."""
    try:
        if item.type == "qcm":
            result = await generate_qcm(item.topic, difficulty)
        else:
            result = await generate_plain(item.topic, difficulty)
        return result
    except Exception as e:
        logging.error(f"Erreur lors de la génération de {item.topic} : {e}")
        return None
