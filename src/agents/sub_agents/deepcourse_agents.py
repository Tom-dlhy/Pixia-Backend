"""Deep course generation sub-agent."""

from typing import Any, Optional

from google.adk.agents import LlmAgent
from google.adk.tools import ToolContext
from google.adk.tools.base_tool import BaseTool

from src.config import gemini_settings
from src.prompts import AGENT_PROMPT_DeepcourseAgent
from src.tools.deepcourse_tools import generate_deepcourse


async def _skip_deepcourse_summarization(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    """
    Skip summarization of deep course tool response.

    Allows passing raw tool response to LLM without automatic summarization,
    preserving the integrity of structured deep course data.

    Args:
        tool: The tool that was called.
        args: Arguments passed to the tool.
        tool_context: Tool context containing actions.
        tool_response: Raw response from the tool.

    Returns:
        None (disables summarization).
    """
    # Enable skip_summarization flag in actions
    tool_context.actions.skip_summarization = True
    return None


deepcourse_agent = LlmAgent(
    name="DeepcourseAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans la génération de deepcourses.",
    instruction=AGENT_PROMPT_DeepcourseAgent,
    tools=[generate_deepcourse],
    # TODO: Callback commented out due to unexpected behavior.
    # after_tool_callback=_skip_deepcourse_summarization,
)
