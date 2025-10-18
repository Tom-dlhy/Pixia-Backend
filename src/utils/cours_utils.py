from src.config import gemini_settings
from src.models import CoursePlan, CourseSynthesis, ChaptersPlanItem, Chapter, Chapter_Schema
from src.prompts import SYSTEM_PROMPT_PLANNER_COURS, SYSTEM_PROMPT_GENERATE_CHAPTER, SYSTEM_PROMPT_GENERATE_IMAGE_CHAPTER
import logging, asyncio
import base64
import uuid
from google.genai import types

logging.basicConfig(level=logging.INFO)

def generate_chapter(title: str, content: str, difficulty: str) -> Chapter:
    """Génère le contenue d'un chapitre basé sur la description fournie.

    Args:
        title (str): Titre du chapitre à générer.
        content (str): Explication du contenu du chapitre à générer.
        difficulty (str): Niveau de difficulté du cours dans lequel le chapitre s'inscrit.

    Returns:
        dict: Dictionnaire représentant le chapitre généré.
    """

    prompt = f"Titre: {title}\nDescription: {content}\nDifficulté: {difficulty}"

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT_GENERATE_CHAPTER,
            "response_mime_type": "application/json",
            "response_schema": Chapter,
        },
    )
    logging.info(f"Response: {response}")
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
        logging.info(f"Réponse générée : {data}")

    except Exception as err:
        logging.error(f"Erreur parsing {err}")

    return data


def generate_schema_for_chapter(chapter: Chapter) -> Chapter_Schema:
    """Génère une image schématique pour un chapitre donné.

    Args:
        chapter (Chapter): Chapitre pour lequel générer le schéma.

    Returns:
        dict: Dictionnaire représentant le schéma généré.
    """

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_IMAGE,
        contents=SYSTEM_PROMPT_GENERATE_IMAGE_CHAPTER + "\n" + chapter.content,
        config=types.GenerateContentConfig(
            response_modalities=['Image'],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
            )
        )
    )
    
    uuid_schema = str(uuid.uuid4())
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            with open(f"{uuid_schema}_generated_image.png", "wb") as f:
                f.write(part.inline_data.data)
            print(f"Image enregistrée sous '{uuid_schema}_generated_image.png'")

            return Chapter_Schema(
                id_schema=uuid_schema,
                id_chapter=chapter.id_chapter,
                img_base64=base64.b64encode(part.inline_data.data).decode('utf-8')
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


async def generate_for_chapter(item: ChaptersPlanItem, difficulty: str, ) -> Chapter:
    """Génère un chapitre pour un sujet donné."""
    try:
        logging.info(f"Génération du chapitre : {item.title}")

        chapter = await asyncio.to_thread(generate_chapter, item.title, item.content, difficulty)
        if hasattr(chapter, "id_chapter") and getattr(chapter, "id_chapter") in (None, ""):
            setattr(chapter, "id_chapter", str(uuid.uuid4()))

        Chapter_Schema = await asyncio.to_thread(generate_schema_for_chapter, chapter)
        setattr(chapter, "id_schema", Chapter_Schema.id_schema)

        return chapter
    except Exception as e:
        logging.error(f"Erreur lors de la génération de {item.title} : {e}")
        return None
    
