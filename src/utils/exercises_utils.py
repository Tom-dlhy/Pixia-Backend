"""
Exercise generation utilities using Google Gemini API.

Provides functions to generate different types of exercises (open-ended questions,
MCQ, and exercise plans) using Gemini models with JSON schema validation.
"""

import json
import logging
import re
from typing import Any, Union

from src.config import gemini_settings
from src.models import (
    ExerciseOutput,
    ExercisePlan,
    ExercicePlanItem,
    ExerciseSynthesis,
    Open,
    QCM,
)
from src.prompts import (
    SYSTEM_PROMPT_OPEN,
    SYSTEM_PROMPT_QCM,
    SYSTEM_PROMPT_PLANNER_EXERCISES,
)

logger = logging.getLogger(__name__)


def _truncate_json_explanations(json_text: str, max_length: int = 1500) -> str:
    """
    Truncate overly long JSON explanation fields to prevent corruption.

    Finds and truncates 'explanation' fields that exceed max_length limit.

    Args:
        json_text: JSON string to process
        max_length: Maximum length for explanations (default: 1500)

    Returns:
        JSON string with truncated explanations
    """
    try:
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
        logger.warning(f"Error truncating JSON explanations: {e}")
        return json_text


async def generate_plain(prompt: str, difficulty: str) -> Union[Open, dict, Any]:
    """
    Generate open-ended exercise questions.

    Creates open-response questions based on provided topic description using
    Gemini API with Open schema validation.

    Args:
        prompt: Detailed description of exercise topic
        difficulty: Difficulty level

    Returns:
        Open model instance or dict representing generated questions
    """
    prompt = f"Description: {prompt}\nDifficulty: {difficulty}"

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
            logger.error("[generate_plain] Response is None")
            return {}

        data = response.parsed
        if not data:
            logger.warning("[generate_plain] response.parsed is None, trying response.text")
            if hasattr(response, "text") and response.text:
                try:
                    raw_text = response.text
                    raw_text = _truncate_json_explanations(raw_text, max_length=1500)
                    raw_data = json.loads(raw_text)
                    data = Open.model_validate(raw_data)

                except json.JSONDecodeError as json_err:
                    logger.error(f"[generate_plain] Invalid JSON: {json_err}")
                    return None
                except Exception as parse_err:
                    logger.error(f"[generate_plain] Manual parsing failed: {parse_err}")
                    return None
            else:
                logger.error("[generate_plain] No valid data in response")
                return None

        return data

    except Exception as err:
        logger.error(f"[generate_plain] Error: {err}")
        return None


async def generate_qcm(prompt: str, difficulty: str) -> Union[QCM, dict, Any]:
    """
    Generate multiple-choice question (MCQ) exercises.

    Creates MCQ-format exercises based on provided topic description using
    Gemini API with QCM schema validation.

    Args:
        prompt: Detailed description of exercise topic
        difficulty: Difficulty level 

    Returns:
        QCM model instance or dict representing generated questions
    """
    prompt = f"Description: {prompt}\nDifficulty: {difficulty}"

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
            logger.error("[generate_qcm] Response is None")
            return {}

        data = response.parsed
        if not data:
            logger.warning("[generate_qcm] response.parsed is None, trying response.text")
            if hasattr(response, "text") and response.text:
                try:
                    raw_text = response.text
                    raw_text = _truncate_json_explanations(raw_text, max_length=1500)
                    raw_data = json.loads(raw_text)
                    data = QCM.model_validate(raw_data)

                except json.JSONDecodeError as json_err:
                    logger.error(f"[generate_qcm] Invalid JSON: {json_err}")
                    return None
                except Exception as parse_err:
                    logger.error(f"[generate_qcm] Manual parsing failed: {parse_err}")
                    return None
            else:
                logger.error("[generate_qcm] No valid data in response")
                return None

        return data

    except Exception as err:
        logger.error(f"[generate_qcm] Error: {err}")
        return None


async def planner_exercises_async(
    synthesis: ExerciseSynthesis,
) -> Union[ExercisePlan, dict, Any]:
    """
    Generate exercise plan asynchronously using Gemini API.

    Creates a structured exercise plan without blocking the event loop.

    Args:
        synthesis: ExerciseSynthesis containing title, description,
                   difficulty, number of exercises, and exercise type

    Returns:
        ExercisePlan model instance with structured exercise plan

    Raises:
        ValueError: If Gemini API call fails or returns invalid response
    """
    logger.info(
        f"[Planner] Starting plan generation - Title: {synthesis.title}, "
        f"Difficulty: {synthesis.difficulty}, Count: {synthesis.number_of_exercises}"
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
        logger.error(f"[Planner] Gemini API call failed: {err}")
        raise ValueError(f"Gemini API call failed: {err}")

    if not response:
        logger.error("[Planner] Response object is None or empty")
        raise ValueError("Gemini returned empty response")

    try:
        data = response.parsed
        if not data:
            logger.warning("[Planner] response.parsed is None, trying response.text")
            if hasattr(response, "text") and response.text:
                logger.info("[Planner] Attempting manual text parsing")
                try:
                    data = ExercisePlan.model_validate_json(response.text)
                    logger.info("[Planner] Manual parsing succeeded")
                    return data
                except Exception as parse_err:
                    logger.error(f"[Planner] Manual parsing failed: {parse_err}")
                    logger.error(f"[Planner] Response text: {response.text[:500]}...")

            logger.error("[Planner] response.parsed is None and no valid alternative found")
            raise ValueError("Planner returned None - no valid data in response")

        logger.info("[Planner] Plan generated successfully")
        return data

    except Exception as err:
        logger.error(f"[Planner] Parsing error: {err}")
        logger.error(f"[Planner] Response type: {type(response)}")
        if hasattr(response, "__dict__"):
            logger.error(f"[Planner] Response attributes: {list(response.__dict__.keys())}")
        raise


async def generate_for_topic(
    item: ExercicePlanItem, difficulty: str
) -> Union[ExerciseOutput, dict, Any, None]:
    """
    Generate exercise (MCQ or open-ended) for given topic.

    Routes to appropriate generator based on exercise type.

    Args:
        item: ExercicePlanItem with topic and exercise type
        difficulty: Difficulty level for generated exercise

    Returns:
        ExerciseOutput instance or None if generation fails
    """
    try:
        if item.type == "qcm":
            result = await generate_qcm(item.topic, difficulty)
        else:
            result = await generate_plain(item.topic, difficulty)

        if result is None:
            logger.error(f"❌ [{item.type}] Generation failed for: {item.topic[:50]}")
            return None

        if isinstance(result, dict) and "type" not in result:
            logger.error(f"❌ [{item.type}] Result missing 'type' field: {item.topic[:50]}")
            return None

        return result

    except Exception as e:
        logger.error(f"❌ Error generating exercise '{item.topic[:50]}...': {e}")
        return None

