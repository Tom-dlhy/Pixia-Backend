from .exercises_prompt import (
    SYSTEM_PROMPT_PLANNER_EXERCISES,
    SYSTEM_PROMPT_OPEN,
    SYSTEM_PROMPT_QCM,
    AGENT_PROMPT_ExerciseAgent,
)

from .cours_prompt import (
    SYSTEM_PROMPT_GENERATE_CHAPTER,
    SYSTEM_PROMPT_GENERATE_IMAGE_CHAPTER,
    SYSTEM_PROMPT_PLANNER_COURS,
    AGENT_PROMPT_CourseAgent,
)

from .orchestrator_prompt import AGENT_PROMPT_ORCHESTRATOR
from .normal_agent_prompt import AGENT_PROMPT_NORMAL_AGENT
from .copilote_prompt import (
    AGENT_PROMPT_CopiloteExerciceAgent_base,
    AGENT_PROMPT_CopiloteCourseAgent_base,
    AGENT_PROMPT_CopiloteDeepCourseAgent_base,
    build_copilot_exercice_system_prompt,
)


__all__ = [
    "SYSTEM_PROMPT_OPEN",
    "SYSTEM_PROMPT_QCM",
    "SYSTEM_PROMPT_PLANNER_EXERCISES",
    "AGENT_PROMPT_ORCHESTRATOR",
    "AGENT_PROMPT_ExerciseAgent",
    "AGENT_PROMPT_CopiloteExerciceAgent_base",
    "build_copilot_exercice_system_prompt",
    "AGENT_PROMPT_CopiloteCourseAgent_base",
    "AGENT_PROMPT_CopiloteDeepCourseAgent_base",
    "AGENT_PROMPT_NORMAL_AGENT",
    "SYSTEM_PROMPT_GENERATE_CHAPTER",
    "SYSTEM_PROMPT_GENERATE_IMAGE_CHAPTER",
    "SYSTEM_PROMPT_PLANNER_COURS",
    "AGENT_PROMPT_CourseAgent",
]
