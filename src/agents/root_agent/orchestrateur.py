from google.adk.agents import LlmAgent
from src.agents.prompts import SYS_PROMPT_ORCHESTRATEUR
from src.config import gemini_settings

root_agent = LlmAgent(
    name="root_agent",
    description="Agent principal qui gère les requêtes et redirige vers les sous-agents appropriés.",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    instruction=SYS_PROMPT_ORCHESTRATEUR,
)
