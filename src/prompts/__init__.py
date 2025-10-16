from .exercises_prompt import SYSTEM_PROMPT_PLANNER_EXERCISES, SYSTEM_PROMPT_OPEN, SYSTEM_PROMPT_QCM, AGENT_PROMPT_ExerciseGenerationAgent, AGENT_PROMPT_ExercisePrecisionAgent
from .orchestrator_prompt import AGENT_PROMPT_ORCHESTRATOR
from .copilote_prompt import AGENT_PROMPT_CopiloteExerciceAgent_base, AGENT_PROMPT_CopiloteCourseAgent_base, AGENT_PROMPT_CopiloteDeepCourseAgent_base, build_copilot_exercice_system_prompt

__all__ = [
    "SYSTEM_PROMPT_OPEN",
    "SYSTEM_PROMPT_QCM",
    "SYSTEM_PROMPT_PLANNER_EXERCISES",
    "AGENT_PROMPT_ORCHESTRATOR",
    "AGENT_PROMPT_ExerciseGenerationAgent",
    "AGENT_PROMPT_ExercisePrecisionAgent",
    "AGENT_PROMPT_CopiloteExerciceAgent_base",
    "build_copilot_exercice_system_prompt",
    "AGENT_PROMPT_CopiloteCourseAgent_base",
    "AGENT_PROMPT_CopiloteDeepCourseAgent_base"
]