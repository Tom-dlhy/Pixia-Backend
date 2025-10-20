from src.config import gemini_settings
from src.prompts import SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION
import logging
from google.genai import types


def agent_correct_plain_question(answer: str, question: str, response: str) -> bool:
    
    prompt = f"Question: {question}\nRéponse correcte: {response}\nRéponse de l'utilisateur: {answer}"

    response = gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION,
            response_modalities=['Text'],
            max_output_tokens=1,
        )
    )
    logging.info(f"Response: {response}")
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
        logging.info(f"Réponse générée : {data}")

    except Exception as err:
        logging.error(f"Erreur parsing {err}")
        data = {}
    
    if isinstance(data, str):
        data = data.strip().lower() in ['true', 'vrai', 'yes', 'oui']
        return data
    else:
        logging.error(f"Erreur: réponse inattendue {data}")
        return False

 

