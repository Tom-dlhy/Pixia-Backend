"""Course generation sub-agent."""

from google.adk.agents import LlmAgent

from src.config import gemini_settings
from src.prompts import AGENT_PROMPT_CourseAgent
from src.tools.cours_tools import generate_courses


course_agent = LlmAgent(
    name="CourseAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans la génération de cours.",
    instruction=AGENT_PROMPT_CourseAgent,
    tools=[generate_courses],
    # Disable transfer back to parent after tool execution.
    # Once the agent completes its tool, we catch the output separately
    # and don't want further communication with this agent.
    disallow_transfer_to_parent=True,
)
