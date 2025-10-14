from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_ExercisePrecisionAgent, AGENT_PROMPT_ExerciseGenerationAgent
from src.config import gemini_settings
from src.tools.exercises_tools import generate_exercises

exercise_generation_agent = LlmAgent(
    name="ExerciseGenerationAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
    description="Agent spécialisé dans la génération d'exercices.",
    instruction=AGENT_PROMPT_ExerciseGenerationAgent,
    tools=[generate_exercises]
)

exercise_precision_agent = LlmAgent(
    name="ExercisePrecisionAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
    description="Agent spécialisé dans la génération d'exercices.",
    instruction=AGENT_PROMPT_ExercisePrecisionAgent,
    sub_agents=[exercise_generation_agent],
)
