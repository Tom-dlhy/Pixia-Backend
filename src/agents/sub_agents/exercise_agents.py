from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_ExerciseAgent
from src.config import gemini_settings
from src.tools.exercises_tools import generate_exercises


exercise_agent = LlmAgent(
    name="ExercisePrecisionAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans la génération d'exercices.",
    instruction=AGENT_PROMPT_ExerciseAgent,
    tools=[generate_exercises],
    disallow_transfer_to_parent=True,
)
