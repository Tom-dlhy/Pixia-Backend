from fastapi import APIRouter
from src.dto import CorrectPlainQuestionRequest, CorrectPlainQuestionResponse
from src.bdd import DBManager
from src.config import gemini_settings
from src.prompts import SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION
import logging
from google.genai import types

router = APIRouter(prefix="/correctplainquestion", tags=["CorrectPlainQuestion"])

#########################
# il faut ajouter la fonctionnalité qui met a jour le content du document dans la bdd avec le status corrigé
#########################

@router.post("", response_model=CorrectPlainQuestionResponse)
async def correct_plain_question(req: CorrectPlainQuestionRequest):
    db_manager = DBManager()
    doc_id = req.doc_id
    
    answer = req.answer
    question = req.question
    response = req.response

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
        return CorrectPlainQuestionResponse(is_correct=data)
    else:
        logging.error(f"Erreur: réponse inattendue {data}")
        return CorrectPlainQuestionResponse(is_correct=False)

 

