from google.adk.agents import LlmAgent

from config import GEMINI_MODEL_2_5_FLASH

root_agent = LlmAgent(
    name="root_agent",
    description="Agent principal qui gère les requêtes et redirige vers les sous-agents appropriés.",
    model=GEMINI_MODEL_2_5_FLASH,
    instruction="""
    Tu es l'agent principal (root_agent) chargé d'orchestrer les interactions entre l'utilisateur et les sous-agents spécialisés.

    Tu dois rediriger les requêtes des utilisateurs vers les sous-agents appropriés en fonction de la nature de la demande.
    N'oublie pas de d'envoyer aux sous agents les informations contextuelles nécessaires pour qu'ils puissent répondre efficacement.
    """,
)
