from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_CopiloteExerciceAgent_base, AGENT_PROMPT_CopiloteCourseAgent_base, AGENT_PROMPT_CopiloteNewChapitreAgent_base
from src.config import gemini_settings
from src.tools.deepcourse_tools import call_generate_new_chapter
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams




copilote_exercice_agent = LlmAgent(
    name="CopiloteExerciceAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans l'assistance à la réalisation d'exercices pour l'utilisateur.",
    instruction=AGENT_PROMPT_CopiloteExerciceAgent_base,
    tools=[],
)

copilote_cours_agent = LlmAgent(
    name="CopiloteCoursAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans l'assistance à un cours pour l'utilisateur.",
    instruction=AGENT_PROMPT_CopiloteCourseAgent_base,
    tools=[
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="https://learn.microsoft.com/api/mcp",
            ),
        )
    ],
)

copilote_new_chapitre_agent = LlmAgent(
    name="CopiloteNewChapitreAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans l'assistance à la réalisation de nouveaux chapitres pour l'utilisateur.",
    instruction=AGENT_PROMPT_CopiloteNewChapitreAgent_base,
    tools=[call_generate_new_chapter],
)
