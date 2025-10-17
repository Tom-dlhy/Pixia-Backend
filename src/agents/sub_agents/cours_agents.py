from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_CoursPrecisionAgent, AGENT_PROMPT_CoursGenerationAgent
from src.config import gemini_settings
from src.tools.cours_tools import generate_courses

cours_generation_agent = LlmAgent(
    name="CoursGenerationAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
    description="Agent spécialisé dans la génération de cours.",
    instruction=AGENT_PROMPT_CoursGenerationAgent,
    tools=[generate_courses]
)

cours_precision_agent = LlmAgent(
    name="CoursPrecisionAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
    description="Agent spécialisé dans la génération de cours.",
    instruction=AGENT_PROMPT_CoursPrecisionAgent,
    sub_agents=[cours_generation_agent],
)

