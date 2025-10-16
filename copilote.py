import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Tuple
from pydantic import BaseModel, Field

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import LlmAgent 
from google.genai import types
from google.genai.types import Part

from dotenv import load_dotenv
from src.models import ExerciseOutput
from src.agents.root_agent import root_agent

from src.prompts import build_copilot_exercice_system_prompt

logging.basicConfig(level=logging.INFO)
load_dotenv()

APP_NAME = "copilote_agent"
USER_ID = "user_123"
SESSION_ID = "session_abc"

async def main():
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
    copilote=None
    print("\n=== Copilote Exo prêt à discuter ===")
    print("Tape 'exit' ou 'quit' pour quitter.\n")

    while True:
        user_input = input("👤 Toi : ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Fin de la session.")
            break

        content = types.Content(role="user", parts=[Part(text=user_input)])

        generate_exercises_output = None
        final_response = None

        async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=content
        ):
            if hasattr(event, "get_function_responses"):
                func_responses = event.get_function_responses()
                if func_responses:
                    for fr in func_responses:
                        name = fr.name
                        resp = fr.response
                        if name == "generate_exercises":
                            logging.info("✅ Tool 'generate_exercises' détecté")
                            generate_exercises_output = resp

            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break

        if generate_exercises_output is not None:
            try:
                if isinstance(generate_exercises_output, list):
                    parsed = [
                        ExerciseOutput(**ex).model_dump() # type: ignore
                        for ex in generate_exercises_output
                    ]
                elif isinstance(generate_exercises_output, dict):
                    parsed = ExerciseOutput(**generate_exercises_output).model_dump()
                else:
                    parsed = generate_exercises_output

            except Exception as e:
                logging.error(f"Erreur parsing ExerciseOutput: {e}")
                parsed = generate_exercises_output
            copilote = next(
                    (
                        a
                        for a in root_agent.sub_agents
                        if getattr(a, "name", None) == "CopiloteExerciceAgent"
                    ),
                    None,
                )
            if copilote and isinstance(copilote, LlmAgent):
                copilote.instruction = build_copilot_exercice_system_prompt(parsed)
                print(copilote.instruction)
            else:
                print("⚠️ Agent copilote non trouvé.")
            print("\n===== Résultat du tool generate_exercises =====")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))

        if final_response:
            print(f"\n🤖 Copilote : {final_response}\n")
        else:
            print("\n⚠️ Aucune réponse du LLM.\n")

        logging.info(f"--- Fin interaction à {datetime.now()} ---\n")
        logging.info(f"Agent qui a rep : {event.author if hasattr(event, 'author') else 'Inconnu'}")
        if copilote is not None:
            logging.info(f"Sys_prompt_cop : {copilote.instruction if copilote and isinstance(copilote, LlmAgent) else 'Inconnu'}")


if __name__ == "__main__":
    asyncio.run(main())