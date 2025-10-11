from google.adk.agents import LlmAgent
from src.agents.prompts import SYS_PROMPT_ORCHESTRATEUR
from src.config import gemini_settings


agent_test = LlmAgent(
    name="agent_test",
    description="Agent qui permet juste de tester des fonctionnalités et des tools.",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    instruction=SYS_PROMPT_ORCHESTRATEUR,
    tools=[],
)
