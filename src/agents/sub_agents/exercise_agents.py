"""Exercise generation sub-agent."""

from google.adk.agents import LlmAgent

from src.config import gemini_settings
from src.prompts import AGENT_PROMPT_ExerciseAgent
from src.tools.exercises_tools import generate_exercises


exercise_agent = LlmAgent(
    name="ExerciseAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans la génération d'exercices.",
    instruction=AGENT_PROMPT_ExerciseAgent,
    tools=[generate_exercises],
    # Disable transfer back to parent after tool execution.
    # Once the agent completes its tool, we catch the output separately
    # and don't want further communication with this agent.
    disallow_transfer_to_parent=True,
)
