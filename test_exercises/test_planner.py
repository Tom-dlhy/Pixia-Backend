from google import genai
from pydantic import BaseModel, Field, StringConstraints
from typing import Annotated
import logging
import time
import json
from src.config import gemini_settings
from test_exercises.plain_text_test import Open, generate_plain
from test_exercises.qcm_test import QCM, generate_qcm
import asyncio

logging.basicConfig(level=logging.INFO)

client = genai.Client(api_key=gemini_settings.GOOGLE_API_KEY)


class ExerciseSynthesis(BaseModel):
    description: Annotated[str, StringConstraints(min_length=10, max_length=500)] = (
        Field(..., description="Description détaillé du sujet des exercices à générer.")
    )
    difficulty: Annotated[str, StringConstraints(min_length=3, max_length=100)] = Field(
        ..., description="Niveau de difficulté de l'exercice"
    )
    number_of_exercises: Annotated[int, Field(ge=1, le=20)] = Field(
        ..., description="Nombre d'exercices à générer (entre 1 et 20)."
    )
    exercise_type: Annotated[str, StringConstraints(pattern="^(qcm|open|both)$")] = (
        Field(..., description="Type d'exercice à générer : qcm / open / both")
    )


class ExercicePlanItem(BaseModel):
    type: Annotated[
        str, StringConstraints(pattern="^(qcm|open)$", strip_whitespace=True)
    ]
    topic: Annotated[str, StringConstraints(min_length=3, max_length=200)]


class ExercisePlan(BaseModel):
    difficulty: Annotated[str, StringConstraints(min_length=3, max_length=100)]
    exercises: list[ExercicePlanItem] = Field(
        ..., min_length=1, max_length=20, description="Liste des exercices à générer."
    )


class ClassifiedPlan(BaseModel):
    qcm: list[ExercicePlanItem] = Field(default_factory=list)
    open: list[ExercicePlanItem] = Field(default_factory=list)


SYSTEM_PROMPT_PLANNER = """
Tu es un assistant pédagogique spécialisé dans la création de plans d'exercices éducatifs.
Ton rôle est de générer un plan clair et progressif d'exercices à partir des paramètres donnés.
Chaque exercice doit avoir un topic différent mais étroitement lié à la description fournie.

Règles :
1. Tous les topics doivent rester dans le même domaine que la description.
2. Les topics doivent être cohérents entre eux et couvrir des sous-thèmes naturels et pertinents du sujet.
3. Si le type est 'both', équilibre entre QCM et questions à réponse ouverte.
4. N'utilise pas de formulations trop longues ou encyclopédiques : privilégie la clarté et la concision.
5. Garde un ton pédagogique adapté au niveau indiqué (ex : Terminale, Université, etc.).
6. Ne répète jamais le même topic ou des variations triviales du même titre.

Exemple :
Description : Les fonctions affines
→ Exemples de bons topics :
  - QCM : Identifier les coefficients d'une fonction affine
  - Open : Déterminer l'équation d'une droite à partir de deux points
"""


def planner(
    description: str, difficulty: str, number_of_exercises: int, exercise_type: str
):
    """
    Génère un plan d'exercice basé sur la description, la difficulté, le nombre d'exercices et le type d'exercice.

    Args:
        description (str): Description détaillée du sujet des exercices à générer.
        difficulty (str): Niveau de difficulté de l'exercice.
        number_of_exercises (int): Nombre d'exercices à générer (entre 1 et 20).
        exercise_type (str): Type d'exercice à générer : qcm / open / both.

    Returns:
        dict: Dictionnaire contenant le plan d'exercice généré.

    """

    start_time = time.time()
    response = client.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=f"Description: {description}\nDifficulté: {difficulty}\nNombre d'exercices: {number_of_exercises}\nType d'exercice: {exercise_type}",
        config={
            "system_instruction": SYSTEM_PROMPT_PLANNER,
            "response_mime_type": "application/json",
            "response_schema": ExercisePlan,
        },
    )
    try:
        data = response.parsed if hasattr(response, "parsed") else response.text
    except Exception as err:
        logging.error(f"Erreur parsing ")
        data = {}
    end_time = time.time()
    logging.info(
        f"Temps de génération du plan d'exercice : {end_time - start_time:.2f} secondes"
    )
    return data


def classify_exercises_type(exercise_plan: ExercisePlan) -> ClassifiedPlan:
    classified = ClassifiedPlan()
    for item in exercise_plan.exercises:
        if item.type == "qcm":
            classified.qcm.append(item)
        elif item.type == "open":
            classified.open.append(item)
    return classified


async def pipeline(
    description: str, difficulty: str, number_of_exercises: int, exercise_type: str
):
    plan_json = planner(description, difficulty, number_of_exercises, exercise_type)

    # Validation du plan
    try:
        if isinstance(plan_json, ExercisePlan):
            plan = plan_json
        elif isinstance(plan_json, dict):
            plan = ExercisePlan.model_validate(plan_json)
        elif isinstance(plan_json, str):
            plan = ExercisePlan.model_validate_json(plan_json)
        else:
            raise TypeError("Format de sortie inattendu.")

        print(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False))
    except Exception as err:
        logging.error(f"Erreur de validation du plan d'exercice: {err}")
        return plan_json

    # Classification
    classified_plan = classify_exercises_type(plan)
    print("\n=== ✅ Plan d'exercice classifié ===\n")
    print(json.dumps(classified_plan.model_dump(), indent=2, ensure_ascii=False))

    # --- Génération asynchrone des exercices ---
    async def generate_for_topic(item: ExercicePlanItem):
        """Génère un exercice (QCM ou Open) pour un sujet donné."""
        try:
            if item.type == "qcm":
                logging.info(f"Génération du QCM : {item.topic}")
                result = await asyncio.to_thread(generate_qcm, item.topic)
            else:
                logging.info(f"Génération du Open : {item.topic}")
                result = await asyncio.to_thread(generate_plain, item.topic)
            return result
        except Exception as e:
            logging.error(f"Erreur lors de la génération de {item.topic} : {e}")
            return None

    # Création des tâches pour tous les exercices du plan
    tasks = [generate_for_topic(ex) for ex in plan.exercises]

    # Exécution en parallèle
    results = await asyncio.gather(*tasks)

    # Filtrage des résultats valides
    generated_exercises = [r for r in results if r is not None]

    print("\n=== ✅ Exercices générés ===\n")

    for idx, ex in enumerate(generated_exercises, start=1):
        try:
            # Extraction du topic
            topic = getattr(ex, "topic", "Sujet inconnu")
            ex_type = getattr(ex, "type", "inconnu").upper()

            print(f"\n--- Exercice {idx} ({ex_type}) ---")
            print(f"Sujet : {topic}\n")

            # Affichage formaté selon le type d'exercice
            if hasattr(ex, "model_dump"):
                data = ex.model_dump()
            else:
                data = ex if isinstance(ex, dict) else json.loads(ex)

            print(json.dumps(data, indent=2, ensure_ascii=False))

        except Exception as err:
            logging.error(f"Erreur d'affichage exercice {idx}: {err}")

    # Retourne les exercices générés
    return generated_exercises


if __name__ == "__main__":

    description = "Les nombres complexes"
    difficulty = "Classe de Terminale"
    number_of_exercises = 4
    exercise_type = "both"

    asyncio.run(pipeline(description, difficulty, number_of_exercises, exercise_type))
