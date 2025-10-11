from pydantic import BaseModel, Field, StringConstraints
from typing import List
from google import genai
from src.config import gemini_settings
from typing import Annotated
import logging, time, json

logging.basicConfig(level=logging.INFO)

client = genai.Client(api_key=gemini_settings.GOOGLE_API_KEY)


class OpenQuestion(BaseModel):
    question: Annotated[str, StringConstraints(min_length=3, max_length=300)]
    answers: str = Field(
        "",
        description="Champ réservé pour la réponse de l'utilisateur, à ne pas remplir",
    )
    explanation: Annotated[str, StringConstraints(min_length=3, max_length=500)]


class Open(BaseModel):
    type: Annotated[str, StringConstraints(pattern="^open$", strip_whitespace=True)]
    topic: Annotated[str, StringConstraints(min_length=3, max_length=200)] = Field(
        ..., description="Titre du bloc de questions"
    )
    questions: List[OpenQuestion] = Field(..., min_length=1, max_length=3)


SYS_PROMPT_PLAIN = """
Tu es un assistant pédagogique spécialisé dans la création de questions à réponse ouverte pour des quiz éducatifs.

Ta mission :
Génère des questions à réponse ouverte à partir du sujet donné dans le prompt, en respectant le schéma fourni.

Règles :
1. Le topic doit être un titre court, clair et directement lié à la question principale.
2. Varie les types de questions :
   - Explication de concepts
   - Raisonnement logique ou démonstration
   - Étude de cas ou mise en situation
   - Résolution de problèmes (pour les disciplines scientifiques)
   - Analyse d’impact ou d’interprétation (pour les matières littéraires, historiques, sociales)
3. La question doit être formulée clairement, avec un niveau adapté à la difficulté spécifiée.
4. L’explication doit être complète et pédagogique : elle peut inclure des formules, du raisonnement, ou des exemples concrets selon la matière.
5. Évite les formulations génériques comme “Expliquez le sujet suivant” ou “Décrivez ce thème”.
6. Garde un ton académique et précis.
"""


def generate_plain(prompt: str):
    """Génère des questions à réponse ouverte basées sur la description de l'exercice fournie.
    Args:
        prompt (str): Description détaillée du sujet des exercices à générer.
    Returns:
        dict: Dictionnaire représentant les questions générées.
    """

    start_time = time.time()
    response = client.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
        contents=prompt,
        config={
            "system_instruction": SYS_PROMPT_PLAIN,
            "response_mime_type": "application/json",
            "response_schema": Open,
        },
    )
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text

    except Exception as err:
        logging.error(f"Erreur parsing ")
        data = {}
    end_time = time.time()
    logging.info(f"Temps de génération du Open : {end_time - start_time:.2f} secondes")
    return data


if __name__ == "__main__":
    prompt = "Génère moi moi 3 questions sur le thème de la Révolution Française."
    qcm_json = generate_plain(prompt)

    # Validation et affichage propre
    try:
        qcm = Open.model_validate(qcm_json)
        print("\n=== ✅ QCM généré avec succès ===\n")
        print(qcm.model_dump_json(indent=2))
    except Exception as e:
        print("\n❌ Erreur lors de la validation du QCM :", e)
        print("\n--- Contenu brut renvoyé par le modèle ---\n")
        print(qcm_json)
