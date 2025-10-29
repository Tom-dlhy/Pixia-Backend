from typing import Optional, Any
from google.adk.agents import LlmAgent
from src.prompts import AGENT_PROMPT_DeepcourseAgent
from src.config import gemini_settings
from src.tools.deepcourse_tools import generate_deepcourse
from google.adk.tools import ToolContext
from google.adk.tools.base_tool import BaseTool


async def _skip_deepcourse_summarization(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    """
    Callback pour sauter la summarization de la réponse du tool deepcourse.
    
    Cela permet de transmettre la réponse brute du tool au LLM sans que celui-ci
    la résume automatiquement, préservant ainsi l'intégrité des données structurées
    du deepcourse.
    
    Args:
        tool: Le tool qui vient d'être appelé
        args: Les arguments passés au tool
        tool_context: Le contexte du tool contenant les actions
        tool_response: La réponse brute du tool
        
    Returns:
        La réponse du tool inchangée (dict)
    """
    # Activer le flag skip_summarization dans les actions
    tool_context.actions.skip_summarization = True
    
    # Retourner la réponse brute du tool
    return None


deepcourse_agent = LlmAgent(
    name="DeepcourseAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans la génération de deepcourses.",
    instruction=AGENT_PROMPT_DeepcourseAgent,
    tools=[generate_deepcourse],
    # after_tool_callback=_skip_deepcourse_summarization,
)
