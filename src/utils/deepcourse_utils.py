from src.config import gemini_settings
import logging, asyncio, uuid
from typing import Any, Optional, List
from src.models import EvaluationOuput, Chapter, PlanDeepcourse, DeepCourseOutput
from src.utils import generate_plain, generate_qcm
from src.prompts import SYSTEM_PROMPT_DEEPCOURSE, SYSTEM_PROMPT_CHAPTER

logging.basicConfig(level=logging.INFO)


def generate_deepcourse(prompt : str, difficulty : str, chapters: Optional[str]) -> DeepCourseOutput:
    """Génère un deepcourse basé sur le niveau de difficulté fourni.

    Args:
        prompt (str): Description détaillée du sujet du deepcourse à générer.
        difficulty (str): Niveau de difficulté du deepcourse.
        chapters (Optional[str]): Liste des titres des chapitres à inclure dans le deepcourse.
        
    Returns:
        Any: Dictionnaire représentant le deepcourse généré.
    """

    plan_deep_course.parsed if hasattr(plan_deep_course, "parsed") else plan_deep_course.text
    for chapter in plan_deep_course:
        description = chapters.get("description", "")
        title = chapter.get("title", "")
        # generate_chapter(description, difficulty, title)

    return plan_deep_course

# def generate_plan_deepcourse(prompt : str, difficulty : str, chapters: Optional[str]) -> PlanDeepcourse:
    
#     prompt = f"""Description: {prompt}\nDifficulté: {difficulty}\n Liste des chapitres : {chapters}"""

#     response = gemini_settings.CLIENT.models.generate_content(
#         model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
#         contents=prompt,
#         config={
#             "system_instruction": SYSTEM_PROMPT_DEEPCOURSE,
#             "response_mime_type": "application/json",
#             "response_schema": PlanDeepcourse,
#         },
#     )
#     try:
#         plan_deep_course = response.parsed if hasattr(response, "parsed") else response.text
#     except Exception as err:
#         logging.error(f"Erreur parsing {err}")
#         plan_deep_course = {}

#     return plan_deep_course


# async def generate_for_topic(item: ExercicePlanItem, difficulty: str) -> ExerciseOutput:
#     """Génère un exercice (QCM ou Open) pour un sujet donné."""
#     try:
#         if item.type == "qcm":
#             logging.info(f"Génération du QCM : {item.topic}")
#             result = await asyncio.to_thread(generate_qcm, item.topic, difficulty)
#         else:
#             logging.info(f"Génération du Open : {item.topic}")
#             result = await asyncio.to_thread(generate_plain, item.topic, difficulty)
#         return result
#     except Exception as e:
#         logging.error(f"Erreur lors de la génération de {item.topic} : {e}")
#         return None

# async def generate_chapter(prompt: str, difficulty: str, chapters: List[str]) -> Chapter:
#     """Génère un chapitre basé sur le niveau de difficulté fourni.

#     Args:
#         prompt (str): Description détaillée du sujet du chapitre à générer.
#         difficulty (str): Niveau de difficulté du chapitre.

#     Returns:
#         Any: Dictionnaire représentant le chapitre généré.
#     """

#     generate_evaluation
#     generate_course
#     generate_exercise

# def generate_evaluation(prompt: str, difficulty: str) -> EvaluationOuput:
#     """Génère une évaluation basée sur le niveau de difficulté fourni.

#     Args:
#         prompt (str): Description détaillée du sujet de l'évaluation à générer.
#         difficulty (str): Niveau de difficulté de l'évaluation.

#     Returns:
#         Any: Dictionnaire représentant l'évaluation générée.
#     """

#     prompt = f"""Description: {prompt}\nDifficulté: {difficulty}\n 
#     Fait en sorte que ce que cette évaluation dure 30 minutes et qu'elle comporte 5 exercices."""

#     return generate_plain(prompt, difficulty) + generate_qcm(prompt, difficulty)
    

# def synthetize_course():
#     pass