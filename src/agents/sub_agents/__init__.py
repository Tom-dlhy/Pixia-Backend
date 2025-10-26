from .exercise_agents import exercise_agent
from .normal_agent import agent_normal
from .exercise_agents import exercise_agent
from .copilote import (
    copilote_exercice_agent,
    copilote_cours_agent,
    copilote_new_chapitre_agent,
)
from .cours_agents import course_agent
from .deepcourse_agents import deepcourse_agent


__all__ = [
    "agent_normal",
    "exercise_agent",
    "copilote_exercice_agent",
    "copilote_cours_agent",
    "copilote_new_chapitre_agent",
    "course_agent",
    "deepcourse_agent",
]
