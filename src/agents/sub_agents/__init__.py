from .exercise_agents import exercise_agent
from .normal_agent import agent_normal
from .exercise_agents import exercise_agent
from .copilote import copilote_exercice_agent, copilote_cours_agent, copilote_deep_course_agent

from .conversational_agents import conversation_precision_agent, speech_conversation_agent, textual_conversation_agent

__all__ = [
    "agent_normal",
    "exercise_agent",
    "copilote_exercice_agent",
    "copilote_cours_agent",
    "copilote_deep_course_agent"

    "conversation_precision_agent",
    "speech_conversation_agent",
    "textual_conversation_agent",
]