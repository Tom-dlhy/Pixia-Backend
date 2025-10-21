from google.adk.agents import LlmAgent
from google.adk.tools import google_search  
from src.config import gemini_settings
from src.tools.normal_tools import construire_prompt_systeme_agent_normal

from src.tools.import_fichier_tools import (
    recevoir_et_lire_pdf,
    resumer_pdfs_session,
    repondre_question_pdf,
)


TOOLS = [
    recevoir_et_lire_pdf,
    resumer_pdfs_session,
    repondre_question_pdf,
]

INSTRUCTION = (
    construire_prompt_systeme_agent_normal(
        sujet="Général",
        niveau="débutant",
        objectifs=["Expliquer clairement", "Donner des exemples simples"],
    )
    + "\n\nPolitique outils (PDF):\n"
    + "- Si la question concerne un document PDF en contexte (résumer, trouver des infos, expliquer), utilise les outils :\n"
    + "  * repondre_question_pdf pour les questions ciblées avec références.\n"
    + "  * resumer_pdfs_session pour produire un résumé concis.\n"
    + "- Pour les questions de suivi sur le même document, continue d'utiliser ces outils (ne redemande pas le fichier)."
)

agent_normal = LlmAgent(
    name="NormalAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,  
    description="Agent généraliste pour discuter et expliquer des notions sans générer d'exercices ni de cours.",
    instruction=INSTRUCTION,
    tools=TOOLS,
)

