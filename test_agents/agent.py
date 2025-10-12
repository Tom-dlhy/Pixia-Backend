import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Tuple

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.types import Part

from dotenv import load_dotenv
from src.models import ExerciseOutput
from src.agents.root_agent import root_agent

logging.basicConfig(level=logging.INFO)
load_dotenv()

APP_NAME = "root_agent2"
USER_ID = "user_123"
SESSION_ID = "session_abc"
JSON_OUTPUT_DIR = Path(__file__).resolve().parent / "json_preview"


async def main():
    # 1. Créer la session
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    # 2. Initialiser le runner
    runner = Runner(
        agent=root_agent, app_name=APP_NAME, session_service=session_service
    )

    # 3. Message utilisateur
    user_input = "Génère 3 exercices sur les nombres complexes niveau terminale avec des QCM et des questions ouvertes."
    content = types.Content(role="user", parts=[Part(text=user_input)])

    # 4. Variables de stockage
    generate_exercises_output = None
    final_response = None

    # 5. Lancement de l'agent
    async for event in runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=content
    ):
        # a) Récupération des tool responses
        if hasattr(event, "get_function_responses"):
            func_responses = event.get_function_responses()
            if func_responses:
                for fr in func_responses:
                    name = fr.name
                    resp = fr.response

                    # ✅ On filtre UNIQUEMENT le tool "generate_exercises"
                    if name == "generate_exercises":
                        logging.info("✅ Tool 'generate_exercises' détecté")
                        generate_exercises_output = resp

        # b) Réponse finale (texte LLM)
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
            break

    # 6. Traitement du résultat du tool
    if generate_exercises_output is not None:
        try:
            # Si le tool renvoie une liste d’exercices
            if isinstance(generate_exercises_output, list):
                parsed = [
                    ExerciseOutput(**ex).model_dump()
                    for ex in generate_exercises_output
                ]
            # Si le tool renvoie un seul exercice
            elif isinstance(generate_exercises_output, dict):
                parsed = ExerciseOutput(**generate_exercises_output).model_dump()
            else:
                parsed = generate_exercises_output  # brut fallback
        except Exception as e:
            logging.error(f"Erreur parsing ExerciseOutput: {e}")
            parsed = generate_exercises_output

        print("\n===== Résultat du tool generate_exercises =====")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))

        try:
            JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = JSON_OUTPUT_DIR / f"{SESSION_ID}_{timestamp}.json"
            output_path.write_text(
                json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logging.info(f"Prévisualisation JSON sauvegardée dans {output_path}")
        except Exception as e:
            logging.error(f"Erreur lors de l'écriture du fichier JSON: {e}")
    else:
        print("\n⚠️ Aucun appel au tool 'generate_exercises' détecté.")

    # 7. Réponse finale du LLM (optionnelle)
    print("\n===== Réponse finale du LLM =====")
    print(final_response)


if __name__ == "__main__":
    asyncio.run(main())
