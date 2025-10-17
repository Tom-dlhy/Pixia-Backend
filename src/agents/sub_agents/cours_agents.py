from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_CoursPrecisionAgent
from src.config import gemini_settings
from src.tools.cours_tools import generate_courses


cours_precision_agent = LlmAgent(
    name="CoursPrecisionAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans la génération de cours.",
    instruction=AGENT_PROMPT_CoursPrecisionAgent,
    tools=[generate_courses],
    disallow_transfer_to_parent=True,
)