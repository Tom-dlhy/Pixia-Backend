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
import logging, asyncio, uuid, re
from typing import Any, Union
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)


def _truncate_json_explanations(json_text: str, max_length: int = 1500) -> str:
    """Tronque les explications JSON trop longues pour éviter les corruptions.

    Cherche les champs 'explanation' et les tronque s'ils dépassent max_length.
    """
    try:
        # Pattern pour trouver "explanation": "..."
        pattern = r'"explanation"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"'

        def truncate_match(match):
            full_match = match.group(0)
            explanation = match.group(1)
            if len(explanation) > max_length:
                truncated = explanation[: max_length - 3] + "..."
                return f'"explanation": "{truncated}"'
            return full_match

        truncated_json = re.sub(pattern, truncate_match, json_text)
        return truncated_json
    except Exception as e:
        logging.warning(f"Erreur lors de la troncature JSON: {e}")
        return json_text


async def generate_plain(prompt: str, difficulty: str) -> Union[Open, dict, Any]:
    """Génère des questions à réponse ouverte basées sur la description de l'exercice fournie.

    Args:
        prompt (str): Description détaillée du sujet des exercices à générer.
        difficulty (str): Niveau de difficulté de l'exercice.

    Returns:
        dict: Dictionnaire représentant les questions générées.
    """

    prompt = f"Description: {prompt}\nDifficulté: {difficulty}"

    try:
        response = await gemini_settings.CLIENT.aio.models.generate_content(
            model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT_OPEN,
                "response_mime_type": "application/json",
                "response_schema": Open,
            },
        )

        if not response:
            logging.error(f"[generate_plain] Response est None")
            return {}

        data = response.parsed
        if not data:
            logging.warning(
                f"[generate_plain] response.parsed est None, tentative avec response.text"
            )
            if hasattr(response, "text") and response.text:
                try:
                    import json

                    raw_text = response.text

                    # Tronquer les explications TRÈS longues AVANT de parser le JSON
                    # pour éviter les corruptions
                    raw_text = _truncate_json_explanations(raw_text, max_length=1500)

                    # Tenter de parser le JSON nettoyé
                    raw_data = json.loads(raw_text)
                    data = Open.model_validate(raw_data)

                except json.JSONDecodeError as json_err:
                    logging.error(f"[generate_plain] JSON invalide: {json_err}")
                    return None
                except Exception as parse_err:
                    logging.error(f"[generate_plain] Échec parsing manuel: {parse_err}")
                    return None
            else:
                logging.error(f"[generate_plain] Aucune donnée valide dans response")
                return None

        return data

    except Exception as err:
        logging.error(f"[generate_plain] Erreur: {err}")
        return None


async def generate_qcm(prompt: str, difficulty: str) -> Union[QCM, dict, Any]:
    """Génère un QCM basé sur la description de l'exercice fournie.

    Args:
        prompt (str): Description détaillée du sujet des exercices à générer.
        difficulty (str): Niveau de difficulté de l'exercice.

    Returns:
        dict: Dictionnaire représentant le QCM généré.
    """

    prompt = f"Description: {prompt}\nDifficulté: {difficulty}"

    try:
        response = await gemini_settings.CLIENT.aio.models.generate_content(
            model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT_QCM,
                "response_mime_type": "application/json",
                "response_schema": QCM,
            },
        )

        if not response:
            logging.error(f"[generate_qcm] Response est None")
            return {}

        data = response.parsed
        if not data:
            logging.warning(
                f"[generate_qcm] response.parsed est None, tentative avec response.text"
            )
            if hasattr(response, "text") and response.text:
                try:
                    import json

                    raw_text = response.text

                    # Tronquer les explications TRÈS longues AVANT de parser le JSON
                    raw_text = _truncate_json_explanations(raw_text, max_length=1500)

                    # Tenter de parser le JSON nettoyé
                    raw_data = json.loads(raw_text)
                    data = QCM.model_validate(raw_data)

                except json.JSONDecodeError as json_err:
                    logging.error(f"[generate_qcm] JSON invalide: {json_err}")
                    return None
                except Exception as parse_err:
                    logging.error(f"[generate_qcm] Échec parsing manuel: {parse_err}")
                    return None
            else:
                logging.error(f"[generate_qcm] Aucune donnée valide dans response")
                return None

        return data

    except Exception as err:
        logging.error(f"[generate_qcm] Erreur: {err}")
        return None


async def planner_exercises_async(
    synthesis: ExerciseSynthesis,
) -> Union[ExercisePlan, dict, Any]:
    """
    Version async de planner_exercises - utilise le client async de Google.

    Génère un plan d'exercice de manière asynchrone sans bloquer le thread.
    """

    # Log des données d'entrée pour debug
    logging.info(
        f"[Planner] Début génération - Title: {synthesis.title}, Difficulté: {synthesis.difficulty}, Nb exercices: {synthesis.number_of_exercises}"
    )

    try:
        response = await gemini_settings.CLIENT.aio.models.generate_content(
            model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
            contents=f"Description: {synthesis.description}\nDifficulté: {synthesis.difficulty}\nNombre d'exercices: {synthesis.number_of_exercises}\nType d'exercice: {synthesis.exercise_type}",
            config={
                "system_instruction": SYSTEM_PROMPT_PLANNER_EXERCISES,
                "response_mime_type": "application/json",
                "response_schema": ExercisePlan,
            },
        )
    except Exception as err:
        logging.error(f"[Planner] Erreur lors de l'appel API Gemini: {err}")
        raise ValueError(f"Gemini API call failed: {err}")

    # Vérification de la réponse
    if not response:
        logging.error(f"[Planner] Response object est None ou vide")
        raise ValueError("Gemini returned empty response")

    # Vérification du parsed
    try:
        data = response.parsed
        if not data:
            # Tentative de récupération via response.text
            logging.warning(
                f"[Planner] response.parsed est None, tentative avec response.text"
            )
            if hasattr(response, "text") and response.text:
                logging.info(f"[Planner] Tentative de parsing manuel du text")
                try:
                    data = ExercisePlan.model_validate_json(response.text)
                    logging.info(f"[Planner] Parsing manuel réussi")
                    return data
                except Exception as parse_err:
                    logging.error(f"[Planner] Échec du parsing manuel: {parse_err}")
                    logging.error(
                        f"[Planner] Response text: {response.text[:500]}..."
                    )  # Log 500 premiers chars

            logging.error(
                f"[Planner] response.parsed est None et aucune alternative valide"
            )
            raise ValueError("Planner returned None - no valid data in response")

        logging.info(f"[Planner] Plan généré avec succès")
        return data

    except Exception as err:
        logging.error(f"[Planner] Erreur parsing: {err}")
        logging.error(f"[Planner] Type de response: {type(response)}")
        if hasattr(response, "__dict__"):
            logging.error(
                f"[Planner] Attributs de response: {list(response.__dict__.keys())}"
            )
        raise


async def generate_for_topic(
    item: ExercicePlanItem, difficulty: str
) -> Union[ExerciseOutput, dict, Any, None]:
    """Génère un exercice (QCM ou Open) pour un sujet donné."""
    try:
        if item.type == "qcm":
            result = await generate_qcm(item.topic, difficulty)
        else:
            result = await generate_plain(item.topic, difficulty)

        # Vérifier que le résultat est valide
        if result is None:
            logging.error(
                f"❌ [{item.type}] Génération échouée pour: {item.topic[:50]}"
            )
            return None

        # Vérifier que le résultat a un champ 'type'
        if isinstance(result, dict) and "type" not in result:
            logging.error(
                f"❌ [{item.type}] Résultat sans 'type' pour: {item.topic[:50]}"
            )
            return None

        return result
    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération de '{item.topic[:50]}...': {e}")
        return None
