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


class QCMAnswer(BaseModel):
    text: Annotated[str, StringConstraints(min_length=1,max_length=300)] # type: ignore
    is_correct: bool = Field(..., description="True si la réponse est correcte")

class QCMQuestion(BaseModel):
    question: Annotated[str, StringConstraints(min_length=3, max_length=300)]
    answers: List[QCMAnswer] = Field(
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
    topic: Annotated[str, StringConstraints(min_length=3, max_length=200)] = Field(
        ...,
        description="Titre du bloc de questions"
    )
    questions: List[QCMQuestion] = Field(..., min_length=1,max_length=10)




SYS_PROMPT_QCM = """
Tu es un assistant pédagogique spécialisé dans la création de QCMs éducatifs clairs et variés.

Ta mission :
Génère un questionnaire à choix multiples (QCM) à partir du sujet donné dans le prompt, en respectant le schéma fourni.

Règles :
1. Le topic doit être un titre court, clair et directement lié à la question principale du QCM.
2. Varie les types de questions :
   - Questions de définition (expliquer un concept)
   - Questions d’application (résoudre un petit problème)
   - Questions d’interprétation (analyser une situation ou un graphique)
   - Questions de comparaison (identifier la bonne relation entre deux notions)
   - Questions de logique ou de piège (choix subtiles mais toujours justes)
3. Alterne entre :
   - Une seule bonne réponse
   - Plusieurs bonnes réponses (multi_answers = true)
4. Les propositions incorrectes doivent être plausibles mais fausses, pas absurdes.
5. L’explication doit être concise et pédagogique : pourquoi la ou les bonnes réponses sont correctes.
6. Évite les répétitions dans la structure des questions.
7. Reste adapté au niveau indiqué (ex : Collège, Lycée, Université).

Exemple :
Topic : Les lois de Newton
→ Bonne diversité :
  - QCM 1 : Identifier la loi correspondant à une situation donnée.
  - QCM 2 : Choisir la formule correcte illustrant la deuxième loi.
  - QCM 3 : Vrai ou faux : "Un objet immobile ne subit aucune force".
"""


def generate_qcm(prompt: str):
    """Génère un QCM basé sur la description de l'exercice fournie.
    Args:
        prompt (str): Description détaillée du sujet des exercices à générer.
    Returns:
        dict: Dictionnaire représentant le QCM généré.
    """

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
