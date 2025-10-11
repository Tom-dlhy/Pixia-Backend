from pydantic import BaseModel, Field
from typing import List, Literal, Union, Optional

from google import genai
from google.genai import types
import logging
import time
import json
logging.basicConfig(level=logging.INFO)

from src.config import gemini_settings

class CourseSynthesis(BaseModel):
    description: str = Field(..., description="Description détaillée du sujet du cours à générer.")
    difficulty: str = Field(..., description="Niveau de difficulté du cours.")
    type: Literal["flash", "standard", "detailed"] = Field("standard", description="Niveau de détail du cours.")

class CoursePlan(BaseModel):
    title: str = Field(..., description="Titre du cours généré.")
    chapters: List[tuple[str, str]] = Field(..., description="Plan du cours sous forme de liste de sections ou chapitres [titre, explication du contenu du chapitre].")
    estimated_duration: Optional[str] = Field(None, description="Durée estimée du cours.")

class Chapter(BaseModel):
    title: str = Field(..., description="Titre du chapitre.")
    content: str = Field(..., description="Contenu détaillé du chapitre.")
    schemas: Optional[List[str]] = Field(None, description="Liste de schémas Mermaid SVG encodés en base64 pour illustrer le chapitre.")

class Course(BaseModel):
    type: Literal["flash", "standard", "detailed"] = Field("standard", description="Niveau de détail du cours.")
    title: str = Field(..., description="Titre du cours généré.")
    outline: List[str] = Field(..., description="Plan du cours sous forme de liste de sections ou chapitres.")
    chapters: List[Chapter] = Field(..., description="Liste des chapitres détaillés du cours.")
    estimated_duration: Optional[str] = Field(None, description="Durée estimée du cours.")

class FlashCourse(BaseModel):
    type: Literal["flash"] = Field("flash", description="Type de cours flash.")
    chapter: Chapter = Field(..., description="Chapitre du cours.")
    estimated_duration: Optional[str] = Field(None, description="Durée estimée du cours.")


SYS_PROMPT_COURSE_PLAN_FLASH = """
Tu es un assistant pédagogique spécialisé dans la création de plans de cours concis et efficaces.
Ta mission :
1. Génère un titre global pour le cours.
3. Crée le cours en un seul chapitre structuré et clair.
 - Le chapitre doit contenir une explication concise et aller à l'essentiel et des exemples pertinents.
 - Le chapitre doit être adapté au niveau de difficulté spécifié.
 - Utilise le tool `generate_mermaid_schema` pour créer autant de schémas Mermaid SVG encodés en base64 afin d'illustrer les concepts clés du chapitre que nécessaire.
4. Fournis une estimation de la durée totale du cours en sachant qu'il ne doit pas excéder 10 minutes.
"""

SYS_PROMPT_COURSE_PLAN_STANDARD = """
Tu es un assistant pédagogique spécialisé dans la création de plans de cours clairs et détaillés.
"""

SYS_PROMPT_COURSE_PLAN_DETAILED = """
Tu es un assistant pédagogique spécialisé dans la création de plans de cours très détaillés et approfondis.
"""

def generate_flash_course(description: str, difficulty: str) -> FlashCourse:

    user_prompt = f"""
    Crée un cours flash sur le sujet suivant : {description}.
    Le cours doit être adapté au niveau de difficulté suivant : {difficulty}.
    Le cours doit être concis, allant à l'essentiel, et ne doit pas dépasser 500 mots.
    Structure le cours en chapitres clairs et logiques.
    Fournis une estimation de la durée totale du cours.
    """

    start_time = time.time()

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=user_prompt,
        config={
            "system_instruction": SYS_PROMPT_COURSE_PLAN_FLASH,
            "response_mime_type": "application/json",
            "response_schema": FlashCourse
        }
    )
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
        print(data)
        
        
    except Exception as err:
        logging.error(f"Erreur parsing ")
        data = {}
    end_time = time.time()
    logging.info(f"Temps de génération du QCM : {end_time - start_time:.2f} secondes")

    return data
        
