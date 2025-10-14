from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_ORCHESTRATOR
from src.config import gemini_settings

agent_test = LlmAgent(
    name="agent_test",
    description="Agent qui permet juste de tester des fonctionnalités et des tools.",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    instruction=AGENT_PROMPT_ORCHESTRATOR,
    tools=[],
)
