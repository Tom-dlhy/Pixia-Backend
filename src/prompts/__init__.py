"""System prompts for AI agents.

Contains all system prompts and agent instructions used to configure LLM agents:
- Orchestrator: Root agent for routing user requests
- Course Agent: Generates educational course content
- Exercise Agent: Generates exercises and QCM questions
- Deep Course Agent: Generates detailed courses with examples
- Copilote Agents: Copilot assistants for various educational tasks
- Utils: Title generation and question correction prompts

IMPORTANT: All prompts are in French and must NOT be translated - they are consumed by LLM models.
"""

from .copilote_prompt import (
    AGENT_PROMPT_CopiloteCourseAgent_base,
    AGENT_PROMPT_CopiloteExerciceAgent_base,
    AGENT_PROMPT_CopiloteNewChapitreAgent_base,
)
from .cours_prompt import (
    AGENT_PROMPT_CourseAgent,
    SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE,
    SYSTEM_PROMPT_GENERATE_MERMAID_CODE,
    SYSTEM_PROMPT_GENERATE_PART,
    SYSTEM_PROMPT_PLANNER_COURS,
)
from .deepcourse_prompt import (
    AGENT_PROMPT_DeepcourseAgent,
    SYSTEM_PROMPT_GENERATE_NEW_CHAPTER,
)
from .exercises_prompt import (
    AGENT_PROMPT_ExerciseAgent,
    SYSTEM_PROMPT_OPEN,
    SYSTEM_PROMPT_PLANNER_EXERCISES,
    SYSTEM_PROMPT_QCM,
)
from .orchestrator_prompt import AGENT_PROMPT_ORCHESTRATOR
from .utils_prompt import (
    GENERATE_TITLE_PROMPT,
    SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION,
)

__all__ = [
    "AGENT_PROMPT_ORCHESTRATOR",
    "AGENT_PROMPT_CourseAgent",
    "AGENT_PROMPT_ExerciseAgent",
    "AGENT_PROMPT_DeepcourseAgent",
    "AGENT_PROMPT_CopiloteExerciceAgent_base",
    "AGENT_PROMPT_CopiloteCourseAgent_base",
    "AGENT_PROMPT_CopiloteNewChapitreAgent_base",
    "GENERATE_TITLE_PROMPT",
    "SYSTEM_PROMPT_CORRECT_PLAIN_QUESTION",
    "SYSTEM_PROMPT_GENERATE_PART",
    "SYSTEM_PROMPT_GENERATE_MERMAID_CODE",
    "SYSTEM_PROMPT_PLANNER_COURS",
    "SYSTEM_PROMPT_GENERATE_COMPLETE_COURSE",
    "SYSTEM_PROMPT_OPEN",
    "SYSTEM_PROMPT_QCM",
    "SYSTEM_PROMPT_PLANNER_EXERCISES",
    "SYSTEM_PROMPT_GENERATE_NEW_CHAPTER",
]
