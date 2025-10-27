from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_DeepcourseAgent
from src.config import gemini_settings
from src.tools.deepcourse_tools import generate_deepcourse

deepcourse_agent = LlmAgent(
    name="DeepcourseAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans la génération de deepcourses.",
    instruction=AGENT_PROMPT_DeepcourseAgent,
    tools=[generate_deepcourse],
)
