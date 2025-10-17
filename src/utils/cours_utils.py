from src.config import gemini_settings
from src.models import CoursePlan, CourseSynthesis, ChaptersPlanItem, Chapter
from src.prompts import SYSTEM_PROMPT_PLANNER_COURS, SYSTEM_PROMPT_GENERATE_CHAPTER
import logging, asyncio

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
        return chapter
    except Exception as e:
        logging.error(f"Erreur lors de la génération de {item.title} : {e}")
        return None
    
