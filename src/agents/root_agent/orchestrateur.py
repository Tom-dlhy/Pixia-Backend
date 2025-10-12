import asyncio

from google.adk.agents import LlmAgent
from google.genai import types
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from src.config import gemini_settings
from src.tools.exercises_tools.generate_exercices_tool import generate_exercises
from src.models.exercise_models import ExerciseOutput
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

APP_NAME="Hackathon-App"
USER_ID="user1234"
SESSION_ID="1234"


exercise_generation_agent = LlmAgent(
    name="ExerciseGenerationAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
    description="Agent spécialisé dans la génération d'exercices.",
    instruction="""
    Tu es un agent spécialisé dans la génération d'exercices.
    Utilise exclusivement le tool `generate_exercises` avec les paramètres fournis.
    Tu ne dois rien reformater, rien expliquer, ni ajouter de texte autour.
    Tu dois **restituer exactement le JSON retourné par le tool**, sans le modifier.

    - N’ajoute pas d’en-tête, pas de texte avant ni après.
    - Ne reformule pas.
    - Ne fais aucune interprétation.
    - Si le tool renvoie du JSON, tu dois simplement le répéter tel quel.
    """,
    tools=[generate_exercises],
    
)

exercise_precision_agent = LlmAgent(
    name="ExercisePrecisionAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
    description="Agent spécialisé dans la génération d'exercices.",
    instruction="""
    Tu dois vérifier que la demande de l'utilisateur est clair et complète pour utiliser appeler le sub_agent `exercise_generation_agent`.
    Si ce n'est pas le cas, pose des questions à l'utilisateur pour clarifier la demande.
    Une fois la demande claire, utilise le sub_agent `exercise_generation_agent` pour générer les exercices demandés.

    Tu dois obtenir les informations suivantes:
    - description (le sujet plus ou moins précis des exercices à générer)
    - difficulty (le niveau de difficulté des exercices, par exemple "college 4e", "lycée terminale", "débutant", "intermédiaire", "avancé", etc.)
    - number_of_exercises (le nombre d'exercices à générer)
    - exercise_type :
        - "qcm" pour des exercices à choix multiples
        - "questions ouvertes/ questions libres etc." -> "open" pour des exercices ouverts
        - "les 2/ questions ouvertes et QCM" -> "both" pour un mélange des deux types

    Voici des exemples de demande de clarification:
    - "Pourriez-vous être plus précis sur le sujet des exercices ?"
    - "Quel niveau de difficulté souhaitez-vous pour les exercices ? (Exemples : 'college 4e', 'lycée terminale', 'débutant', 'intermédiaire', 'avancé')"
    - "Combien d'exercices souhaitez-vous générer ?"
    - "Quel type d'exercices préférez-vous ? (qcm, open, ou les deux)"

    À chaque fois que tu demande des clarifications, demande toutes les informations manquantes en une seule fois de manière fluide et naturelle.
    Ne fait pas de récapitulatif avant d'appeler le sub_agent, dès que tu as toutes les informations, appelle le sub_agent DIRECTEMENT.
    """,
    sub_agents=[exercise_generation_agent],
)

# Si tu as un agent “root” plus global :
root_agent = LlmAgent(
    name="RootAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    instruction="Orchestre les demandes d'exercice via l'agent `exercise_precision_agent`.",
    sub_agents=[exercise_precision_agent]
)

# ------- Exemple d'exécution -------



# Session and Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService() # Pour le dev uniquement
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner

# Agent Interaction
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)

# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
await call_agent_async("this is urgent, i cant login")


async def main():
    runner = InMemoryRunner(app_name="hackathon-app", agent=root_agent)
    content = types.Content(role="user", parts=[
        types.Part(text="Je veux des exercices de physique sur les forces")
    ])
    result = await runner.run(runner, content)
    print("== Résultat final state ==")
    print(result.session.state)

if __name__ == "__main__":
    asyncio.run(main())
