from google.adk.agents import LlmAgent
from src.config import gemini_settings
from src.agents.sub_agents import exercise_precision_agent, conversation_precision_agent
from src.prompts import AGENT_PROMPT_ORCHESTRATOR

root_agent = LlmAgent(
    name="RootAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    instruction=AGENT_PROMPT_ORCHESTRATOR,
    sub_agents=[conversation_precision_agent]
)
