from .exercises_prompt import (
    SYSTEM_PROMPT_PLANNER_EXERCISES, 
    SYSTEM_PROMPT_OPEN, 
    SYSTEM_PROMPT_QCM, 
    AGENT_PROMPT_ExerciseGenerationAgent, 
    AGENT_PROMPT_ExercisePrecisionAgent
)

from .cours_prompt import (
    SYSTEM_PROMPT_GENERATE_CHAPTER,
    SYSTEM_PROMPT_PLANNER_COURS, 
    AGENT_PROMPT_CoursPrecisionAgent, 
    AGENT_PROMPT_CoursGenerationAgent
)

from .orchestrator_prompt import AGENT_PROMPT_ORCHESTRATOR

__all__ = [
    "SYSTEM_PROMPT_OPEN",
    "SYSTEM_PROMPT_QCM",
    "SYSTEM_PROMPT_PLANNER_EXERCISES",
    "AGENT_PROMPT_ORCHESTRATOR",
    "AGENT_PROMPT_ExerciseGenerationAgent",
    "AGENT_PROMPT_ExercisePrecisionAgent",
    "SYSTEM_PROMPT_GENERATE_CHAPTER",
    "SYSTEM_PROMPT_PLANNER_COURS",
    "AGENT_PROMPT_CoursPrecisionAgent",
    "AGENT_PROMPT_CoursGenerationAgent",
]