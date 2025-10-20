from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_CopiloteExerciceAgent_base, AGENT_PROMPT_CopiloteCourseAgent_base, AGENT_PROMPT_CopiloteDeepCourseAgent_base
from src.config import gemini_settings
from google.adk.tools import google_search
from src.tools.import_fichier_tools import recevoir_et_lire_pdf

copilote_exercice_agent = LlmAgent(
    name="CopiloteExerciceAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans l'assistance à la réalisation d'exercices pour l'utilisateur.",
    instruction=AGENT_PROMPT_CopiloteExerciceAgent_base,
    tools=[
        recevoir_et_lire_pdf,
    ],
    # tools=[google_search]
)

copilote_cours_agent = LlmAgent(
    name="CopiloteCoursAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans l'assistance à un cours pour l'utilisateur.",
    instruction=AGENT_PROMPT_CopiloteCourseAgent_base,
    tools=[
        recevoir_et_lire_pdf,
    ],
    # tools=[google_search]
)

copilote_deep_course_agent = LlmAgent(
    name="CopiloteDeepCourseAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans l'assistance à la réalisation de cours approfondis pour l'utilisateur (exercices + cours).",
    instruction=AGENT_PROMPT_CopiloteDeepCourseAgent_base,
    # tools=[google_search]
    tools=[
        recevoir_et_lire_pdf,
    ],
)