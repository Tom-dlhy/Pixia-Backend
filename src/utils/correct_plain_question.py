"""
Plain text question correction agent.

Uses Gemini API to evaluate user responses against expected answers
for open-ended questions.
"""

import logging
from pydantic import BaseModel
from src.config import gemini_settings
from src.prompts import SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION

logger = logging.getLogger(__name__)

class IsCorrectResponse(BaseModel):
    """Response model for answer correctness validation."""
    is_correct: bool


async def agent_correct_plain_question(
    answer: str, question: str, response: str
) -> bool:
    """
    Evaluate if user answer is correct for an open-ended question.

    Uses Gemini API with structured response schema to validate the answer
    against the expected response. Returns bool indicating correctness.

    Args:
        answer: User's submitted answer
        question: Original question text
        response: Expected/correct answer

    Returns:
        True if answer is correct, False otherwise
    """
    prompt = (
        f"Question: {question}\n"
        f"Expected answer: {response}\n"
        f"User answer: {answer}"
    )

    try:
        api_response = await gemini_settings.CLIENT.aio.models.generate_content(
            model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION,
                "response_mime_type": "application/json",
                "response_schema": IsCorrectResponse,
            },
        )

        parsed = api_response.parsed
        if isinstance(parsed, IsCorrectResponse):
            return parsed.is_correct

        logger.error("Parse error: unexpected response type")
        return False

    except Exception as err:
        logger.error(f"Parse error: {err}")
        return False
