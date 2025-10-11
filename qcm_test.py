from pydantic import BaseModel, Field
from typing import List
from google import genai
from src.config import gemini_settings
from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated
import logging
import time
import json
logging.basicConfig(level=logging.INFO)

client = genai.Client(api_key=gemini_settings.GOOGLE_API_KEY)


class Answer(BaseModel):
    text: Annotated[str, StringConstraints(min_length=1,max_length=300)] # type: ignore
    is_correct: bool = Field(..., description="True si la réponse est correcte")

class Question(BaseModel):
    question: Annotated[str, StringConstraints(min_length=3, max_length=300)]
    answers: List[Answer] = Field(
        ..., 
        min_length=2, 
        max_length=5,
        description="Entre 2 et 5 réponses possibles"
    )
    explanation: Annotated[str, StringConstraints(min_length=3, max_length=500)]
    multi_answers: bool = Field(
        ..., 
        description="True si la question a plusieurs réponses correctes"
    )

class QCM(BaseModel):
    type: Annotated[str, StringConstraints(pattern="^qcm$", strip_whitespace=True)]
    questions: List[Question] = Field(..., min_length=1,max_length=10)




SYS_PROMPT_QCM = """Tu es un assistant spécialisé dans la création de questionnaires à choix multiples (QCM). 
Tu dois générer des QCMs basés sur les instructions données. Respecte le schéma imposé et le thème.
"""



def generate_qcm(prompt: str):


    start_time = time.time()
    response = client.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYS_PROMPT_QCM,
            "response_mime_type": "application/json",
            "response_schema": QCM
        }
    )
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
        
        
    except Exception as err:
        logging.error(f"Erreur parsing ")
        data = {}
    end_time = time.time()
    logging.info(f"Temps de génération du QCM : {end_time - start_time:.2f} secondes")
    return data


if __name__ == "__main__":
    prompt = "Crée un QCM de 5 questions sur le vietnam avec au moins une questions avec plusieurs réponses et une avec une seule réponse."
    qcm_json = generate_qcm(prompt)

    # Validation et affichage propre
    try:
        qcm = QCM.model_validate(qcm_json)
        print("\n=== ✅ QCM généré avec succès ===\n")
        print(qcm.model_dump_json(indent=2))
    except Exception as e:
        print("\n❌ Erreur lors de la validation du QCM :", e)
        print("\n--- Contenu brut renvoyé par le modèle ---\n")
        print(qcm_json)
