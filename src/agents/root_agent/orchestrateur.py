from google.adk.agents import LlmAgent
from src.config import gemini_settings
from src.agents.sub_agents import (
    exercise_agent,
    copilote_exercice_agent,
    copilote_cours_agent,
    copilote_deep_course_agent,
    agent_normal,
    course_agent,
)
from src.prompts import AGENT_PROMPT_ORCHESTRATOR
from src.tools.import_fichier_tools import recevoir_et_lire_pdf

root_agent = LlmAgent(
    name="RootAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    instruction=AGENT_PROMPT_ORCHESTRATOR,
    tools=[
        recevoir_et_lire_pdf,
    ],
    sub_agents=[
        exercise_agent,
        copilote_exercice_agent,
        copilote_cours_agent,
        copilote_deep_course_agent,
        agent_normal,
        course_agent,
    ],
)
