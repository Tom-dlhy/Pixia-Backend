from src.config import gemini_settings
from src.prompts import SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION
import logging
from pydantic import BaseModel


class IsCorrectResponse(BaseModel):
    is_correct: bool

async def agent_correct_plain_question(
    answer: str, question: str, response: str
) -> bool:

    prompt = f"Question: {question}\nRéponse correcte: {response}\nRéponse de l'utilisateur: {answer}"

    api_response = await gemini_settings.CLIENT.aio.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION,
            "response_mime_type": "application/json",
            "response_schema": IsCorrectResponse,
        },
    )
    print(f"Réponse de l'API Gemini: {api_response}")

    try:
        parsed = api_response.parsed
        if isinstance(parsed, IsCorrectResponse):
            return parsed.is_correct
        else:
            logging.error(f"Erreur parsing: réponse inattendue")
            return False
    except Exception as err:
        logging.error(f"Erreur parsing {err}")
        return False
