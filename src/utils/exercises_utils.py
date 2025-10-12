from src.config import gemini_settings
from src.models import Open, QCM, QCM, ExercisePlan, ExercicePlanItem, ExerciseOutput
from src.prompts import SYSTEM_PROMPT_OPEN, SYSTEM_PROMPT_QCM, SYSTEM_PROMPT_PLANNER
import logging, asyncio, uuid
from typing import Any
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

def generate_plain(prompt: str, difficulty: str) -> Open:
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

def generate_qcm(prompt: str, difficulty: str) -> QCM:
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

def planner(
    description: str, difficulty: str, number_of_exercises: int, exercise_type: str
) -> ExercisePlan:
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
        contents=f"Description: {description}\nDifficulté: {difficulty}\nNombre d'exercices: {number_of_exercises}\nType d'exercice: {exercise_type}",
        config={
            "system_instruction": SYSTEM_PROMPT_PLANNER,
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

async def generate_for_topic(item: ExercicePlanItem, difficulty: str) -> ExerciseOutput:
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

def add_uuid_recursive(exercise_output: ExerciseOutput) -> None:
    """
    Parcourt récursivement un objet (BaseModel, dict, list) et ajoute un champ 'id' unique
    à chaque entité Pydantic qui ne possède pas déjà d'ID.

    Args:
        exercise_output (ExerciseOutput): L'objet ExerciseOutput à modifier.
    Returns:
        None: Modifie l'objet en place.
    """
    # Si c'est un modèle Pydantic
    if isinstance(exercise_output, BaseModel):
        # Si l'objet a un champ 'id' et qu'il est vide → on le remplit
        if hasattr(exercise_output, "id") and getattr(exercise_output, "id") in (None, ""):
            setattr(exercise_output, "id", str(uuid.uuid4()))

        # Parcours récursif des champs du modèle
        for field_name, field_value in exercise_output.__dict__.items():
            add_uuid_recursive(field_value)

    # Si c'est une liste → on itère
    elif isinstance(exercise_output, list):
        for item in exercise_output:
            add_uuid_recursive(item)

    # Si c'est un dict → on itère aussi
    elif isinstance(exercise_output, dict):
        for key, value in exercise_output.items():
            add_uuid_recursive(value)

def assign_uuids_to_output(exercise_output: ExerciseOutput) -> ExerciseOutput:
    """
    Ajoute un UUID à tous les niveaux d'un ExerciseOutput complet.

    Args:
        exercise_output (ExerciseOutput): L'objet ExerciseOutput à modifier.

    Returns:
        ExerciseOutput: L'objet ExerciseOutput avec des UUID ajoutés.
    """
    add_uuid_recursive(exercise_output)
    return exercise_output
