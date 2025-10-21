from src.config import gemini_settings
from src.models import CoursePlan, CourseSynthesis, PartSchema, Part, PartPlanItem, CourseOutput
from src.prompts import SYSTEM_PROMPT_PLANNER_COURS,SYSTEM_PROMPT_GENERATE_PART, SYSTEM_PROMPT_GENERATE_IMAGE_PART
import logging, asyncio
import base64
import uuid
from google.genai import types
from typing import Dict, Any
from enum import Enum
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

def generate_part(title: str, content: str, difficulty: str):
    """Génère le contenu d'une partie basé sur la description fournie.

    Args:
        title (str): Titre de la partie à générer.
        content (str): Explication du contenu de la partie à générer.
        difficulty (str): Niveau de difficulté du cours dans lequel la partie s'inscrit.

    Returns:
        dict: Dictionnaire représentant le partie généré.
    """

    prompt = f"Titre: {title}\nDescription: {content}\nDifficulté: {difficulty}"

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT_GENERATE_PART,
            "response_mime_type": "application/json",
            "response_schema": Part,
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


def generate_schema_for_part(course_part: Part) -> PartSchema:
    """Génère une image schématique pour une partie donné.

    Args:
        part (Part): partie pour laquelle générer le schéma.

    Returns:
        dict: Dictionnaire représentant le schéma généré.
    """
    schema_description = ""
    if isinstance(course_part.schema_description, str):
        schema_description = course_part.schema_description
    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_IMAGE,
        contents=SYSTEM_PROMPT_GENERATE_IMAGE_PART + "\n" + schema_description,
        config=types.GenerateContentConfig(
            response_modalities=['Image'],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
            )
        )
    )
    
    uuid_schema = str(uuid.uuid4())
    for response_part in response.candidates[0].content.parts:
        if response_part.text is not None:
            print(response_part.text)
        elif response_part.inline_data is not None:
            
            return PartSchema(
                id_schema=uuid_schema,
                id_part=course_part.id_part,
                img_base64=base64.b64encode(response_part.inline_data.data).decode('utf-8')
            )


def planner_cours(synthesis: CourseSynthesis) -> CoursePlan:
    """
    Génère un plan de cours basé sur la description, la difficulté et le niveau de détail.

    Args:
        description (str): Description détaillée du sujet du cours à générer.
        difficulty (str): Niveau de difficulté du cours.
        level_detail (str): Niveau de détail du cours.

    Returns:
        dict: Dictionnaire contenant le plan de cours généré.

    """

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=f"Description: {synthesis.description}\nDifficulté: {synthesis.difficulty}\nNiveau de détail: {synthesis.level_detail}",
        config={
            "system_instruction": SYSTEM_PROMPT_PLANNER_COURS,
            "response_mime_type": "application/json",
            "response_schema": CoursePlan,
        },
    )
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
    except Exception as err:
        logging.error(f"Erreur parsing {err}")
        data = {}

    return data


async def generate_for_part(item: PartPlanItem, difficulty: str, ) -> Part | None:
    """Génère un partie pour un sujet donné."""
    try:
        logging.info(f"Génération du partie : {item.title}")

        part = await asyncio.to_thread(generate_part, item.title, item.content, difficulty)
        if hasattr(part, "id_part") and getattr(part, "id_part") in (None, ""):
            setattr(part, "id_part", str(uuid.uuid4()))

        Part_Schema = await asyncio.to_thread(generate_schema_for_part, part)
        setattr(part, "id_schema", Part_Schema.id_schema)

        return part
    except Exception as e:
        logging.error(f"Erreur lors de la génération de {item.title} : {e}")
        return None
    

def add_uuid_recursive(course_output: CourseOutput) -> None:
    """
    Parcourt récursivement un objet (BaseModel, dict, list) et ajoute un champ 'id' unique
    à chaque entité Pydantic qui ne possède pas déjà d'ID.

    Args:
        exercise_output (ExerciseOutput): L'objet ExerciseOutput à modifier.
    Returns:
        None: Modifie l'objet en place.
    """
    # Si c'est un modèle Pydantic
    if isinstance(course_output, BaseModel):
        # Si l'objet a un champ 'id' et qu'il est vide → on le remplit
        if hasattr(course_output, "id") and getattr(course_output, "id") in (None, ""):
            setattr(course_output, "id", str(uuid.uuid4()))

        # Parcours récursif des champs du modèle
        for field_name, field_value in course_output.__dict__.items():
            add_uuid_recursive(field_value)

    # Si c'est une liste → on itère
    elif isinstance(course_output, list):
        for item in course_output:
            add_uuid_recursive(item)

    # Si c'est un dict → on itère aussi
    elif isinstance(course_output, dict):
        for key, value in course_output.items():
            add_uuid_recursive(value)

def assign_uuids_to_output_course(course_output: CourseOutput) -> CourseOutput:
    """
    Ajoute un UUID à tous les niveaux d'un CourseOutput complet.

    Args:
        course_output (CourseOutput): L'objet CourseOutput à modifier.

    Returns:
        CourseOutput: L'objet CourseOutput avec des UUID ajoutés.
    """
    add_uuid_recursive(course_output)
    return course_output
