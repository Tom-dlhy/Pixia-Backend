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
from src.tools.import_fichier_tools import recevoir_et_lire_pdf, resumer_pdfs_session, repondre_question_pdf

PDF_TOOLS_POLICY = (
    "\n\nPolitique outils (PDF):\n"
    "- Si la demande concerne un document PDF en contexte (résumer, trouver des infos, expliquer), utilise les outils :\n"
    "  * repondre_question_pdf pour les questions ciblées avec références.\n"
    "  * resumer_pdfs_session pour produire un résumé concis.\n"
    "- Pour les questions de suivi sur le même document, continue d'utiliser ces outils (ne redemande pas le fichier)."
)

root_agent = LlmAgent(
    name="RootAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    instruction=AGENT_PROMPT_ORCHESTRATOR + PDF_TOOLS_POLICY,
    tools=[
        recevoir_et_lire_pdf,
        resumer_pdfs_session,
        repondre_question_pdf,
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
