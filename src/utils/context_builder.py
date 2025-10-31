"""Context building utilities for agent orchestration.

This module provides utilities to construct agent context from JSON message data,
including agent indication, user information, and study difficulty level.
"""

import json
from typing import Optional


async def final_context_builder(message_context: Optional[str]) -> str:
    """Build agent context string from JSON message data.

    Constructs a context string containing:
    - Agent indication (routing information)
    - User full name
    - Study difficulty level

    Args:
        message_context: Optional JSON string containing context data

    Returns:
        Formatted context string for agent orchestration
    """
    context_dict = {}
    if message_context:
        context_dict = json.loads(message_context)

    agent_indication = context_dict.get("agentIndication")
    user_full_name = context_dict.get("userFullName")
    user_study = context_dict.get("userStudy")

    contextText=""
    match agent_indication:
        case "chat":
            contextText += "- Tu es le RootAgent.\n"
        case "cours":
            contextText += "- Redirige la demande vers le CourseAgent.\n"
        case "exercice":
            contextText += "- Redirige la demande vers le ExerciseAgent.\n"
        case "copiloteCours":
            contextText += "- Redirige la demande vers le CopiloteCoursAgent.\n"
        case "copiloteExercice":
            contextText += "- Redirige la demande vers le CopiloteExerciceAgent.\n"
        case "copiloteNouveauCours":
            contextText += "- Redirige la demande vers le CopiloteNewChapitreAgent.\n"
        case "deepCourse":
            contextText += "- Redirige la demande vers le DeepCourseAgent.\n"

    if user_full_name:
        contextText += f"- L'utilisateur s'appelle {user_full_name}.\n"
    if user_study:
        contextText += f"- Le niveau de difficulté pour les cours et exercices est reglé sur {user_study}.\n"

    if contextText != "":
        contextText = "Contexte supplémentaire pour les agents:\n" + contextText + "\n --- \n\n"


    return contextText