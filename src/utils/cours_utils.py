from src.config import gemini_settings
from src.models import CoursePlan, CourseSynthesis, PartSchema, Part, PartPlanItem, CourseOutput
from src.prompts import SYSTEM_PROMPT_PLANNER_COURS,SYSTEM_PROMPT_GENERATE_PART, SYSTEM_PROMPT_GENERATE_MERMAID_CODE
import logging, asyncio
import base64
from uuid import uuid4
from google.genai import types
from typing import Dict, Any, Union, Optional
from enum import Enum
from pydantic import BaseModel
import os, hashlib, subprocess


logging.basicConfig(level=logging.INFO)

def generate_part(title: str, content: str, difficulty: str) -> Union[Part, dict, Any]:
    """Génère le contenu d'une partie basé sur la description fournie.

    Args:
        title (str): Titre de la partie à générer.
        content (str): Explication du contenu de la partie à générer.
        difficulty (str): Niveau de difficulté du cours dans lequel la partie s'inscrit.

    Returns:
        Union[Part, dict, Any]: Partie générée (Part model, dict, ou autre réponse API).
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

def generate_schema_mermaid(mermaid_code: str) :
    """
    Envoie le code Mermaid à Kroki via curl, récupère le SVG et l'enregistre dans folder_path.
    Retourne le fichier SVG créé en base 64.
    """
    folder_path="."
    os.makedirs(folder_path, exist_ok=True)

    digest = hashlib.sha256(mermaid_code.encode("utf-8")).hexdigest()[:16]
    out_path = os.path.join(folder_path, f"mermaid_{digest}.svg")

    cmd = [
        "curl", "-sS", "-f",
        "-X", "POST",
        "-H", "Content-Type: text/plain",
        "https://kroki.io/mermaid/svg",
        "--data-binary", "@-",
    ]
    proc = subprocess.run(
        cmd,
        input=mermaid_code.encode("utf-8"),
        capture_output=True,
        check=False,
    )

    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"curl a échoué (exit {proc.returncode}) : {err or 'aucun message'}")
    try :
        with open(out_path, "wb") as f:
            f.write(proc.stdout)
        with open(out_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("ascii")
    finally:
        try: 
            os.remove(out_path)
        except Exception as e:
            logging.warning(f"Impossible de supprimer le {out_path}: {e}")
        
    return image_b64

def generate_mermaid_schema_description(course_part: Part):
    """
    Génère 
    """
    schema_description = ""
    if isinstance(course_part.schema_description, str):
        schema_description = course_part.schema_description
        try:
            response = gemini_settings.CLIENT.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=SYSTEM_PROMPT_GENERATE_MERMAID_CODE + "\n" + schema_description,
                config=types.GenerateContentConfig(
                    response_modalities=['Text'],
                )
            )
            uuid_schema = str(uuid4())
            mermaid_code = ""
            if getattr(response, "candidates", None):
                for cand in response.candidates:
                    content = getattr(cand, "content", None)
                    if content and getattr(content, "parts", None):
                        for p in content.parts:
                            if getattr(p, "text", None):
                                mermaid_code += p.text

            mermaid_code = (mermaid_code or "").strip()
            if not mermaid_code:
                logging.error("Le modèle n'a pas renvoyé de code Mermaid.")
                return None

            img_b64 = generate_schema_mermaid(mermaid_code)
        except Exception as e:
            logging.info("Erreur")

    return PartSchema(
        id_schema=uuid_schema,
        id_part=course_part.id_part,
        img_base64=img_b64
    )

# def generate_schema_for_part(course_part: Part) -> Optional[PartSchema]:
#     """Génère une image schématique pour une partie donné.

#     Args:
#         part (Part): partie pour laquelle générer le schéma.

#     Returns:
#         Optional[PartSchema]: Schéma généré ou None en cas d'erreur.
#     """
#     schema_description = ""
#     if isinstance(course_part.schema_description, str):
#         schema_description = course_part.schema_description
    
#     try:
#         response = gemini_settings.CLIENT.models.generate_content(
#             model=gemini_settings.GEMINI_MODEL_2_5_FLASH_IMAGE,
#             contents=SYSTEM_PROMPT_GENERATE_IMAGE_PART + "\n" + schema_description,
#             config=types.GenerateContentConfig(
#                 response_modalities=['Image'],
#                 image_config=types.ImageConfig(
#                     aspect_ratio="16:9",
#                 )
#             )
#         )
        
#         uuid_schema = str(uuid.uuid4())

#         if response.candidates and len(response.candidates) > 0:
#             content = response.candidates[0].content
#             if content and content.parts:
#                 for response_part in content.parts:
#                     if response_part.text is not None:
#                         print(response_part.text)
#                     elif response_part.inline_data is not None and response_part.inline_data.data:
#                         return PartSchema(
#                             id_schema=uuid_schema,
#                             id_part=course_part.id_part,
#                             img_base64=base64.b64encode(response_part.inline_data.data).decode('utf-8')
#                         )
#     except Exception as e:
#         logging.error(f"Erreur lors de la génération du schéma: {e}")
    
#     return None


def planner_cours(synthesis: CourseSynthesis) -> Union[CoursePlan, dict, Any]:
    """
    Génère un plan de cours basé sur la description, la difficulté et le niveau de détail.

    Args:
        description (str): Description détaillée du sujet du cours à générer.
        difficulty (str): Niveau de difficulté du cours.
        level_detail (str): Niveau de détail du cours.

    Returns:
        Union[CoursePlan, dict, Any]: Plan de cours généré (CoursePlan model, dict, ou autre réponse API).

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


async def generate_for_part(item: PartPlanItem, difficulty: str) -> Union[Part, dict, Any, None]:
    """Génère un partie pour un sujet donné."""
    try:
        logging.info(f"Génération du partie : {item.title}")

        part = await asyncio.to_thread(generate_part, item.title, item.content, difficulty)
        
        # Convertir en Part si nécessaire
        if isinstance(part, dict):
            part = Part.model_validate(part)
        elif isinstance(part, str):
            part = Part.model_validate_json(part)
        
        if hasattr(part, "id_part") and getattr(part, "id_part") in (None, ""):
            setattr(part, "id_part", str(uuid4()))

        Part_Schema = await asyncio.to_thread(generate_mermaid_schema_description, part)
        if Part_Schema is not None and hasattr(Part_Schema, "id_schema"):
            setattr(part, "id_schema", Part_Schema.id_schema)
        return part
    
    except Exception as e:
        logging.error(f"Erreur lors de la génération de {item.title} : {e}")
        return None
    
