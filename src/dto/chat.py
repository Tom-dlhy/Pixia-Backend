from pydantic import BaseModel
from typing import Optional, List, Literal, Union
from src.models import ExerciseOutput


class LoadFile(BaseModel):
    filename: str
    size: int
    content_type: str


class ChatRequest(BaseModel):
    user_id: str
    message: str
    files: Optional[List[LoadFile]] = []
    session_id: Optional[str] = None


from pydantic import BaseModel
from typing import Literal, Union
from src.models import ExerciseOutput  # à adapter selon ton projet


# ---- 1️⃣ Représente une réponse de l'agent ----
class AgentAnswer(BaseModel):
    """Représente la réponse brute de l'agent avant formatage final."""

    type: Literal["text", "json", "speech"]
    content: Union[str, dict]


# ---- 2️⃣ Structure principale renvoyée au frontend ----
class ChatResponse(BaseModel):
    """Structure mainisée renvoyée au frontend."""

    chat_id: str
    agent_used: str
    scene: Literal[
        "exercise",  # redirection vers la scène exercice
        "course",  # cours simple
        "deep-course",  # cours approfondi
        "discuss-text",  # discussion textuelle
        "discuss-speech",  # discussion orale
        "main",  # chat main
    ]
    answer_type: Literal["text", "exercise", "course", "deep-course"]
    answer: Union[str, ExerciseOutput, None] = None


# ---- 3️⃣ Exemple de fonction utilitaire ----
def build_chat_response(
    chat_id: str,
    agent_used: str,
    raw_answer: ExerciseOutput,
) -> ChatResponse:
    """Construit un ChatResponse à partir de la réponse brute de l'agent."""

    if isinstance(raw_answer, ExerciseOutput):
        return ChatResponse(
            chat_id=chat_id,
            agent_used=agent_used,
            scene="exercise",
            answer_type="exercise",
            answer=raw_answer,
        )

    # elif isinstance(raw_answer, CourseOutput):
    #     return ChatResponse(
    #         chat_id=chat_id,
    #         agent_used=agent_used,
    #         scene="course",
    #         answer_type="course",
    #         answer=raw_answer,
    #     )

    elif isinstance(raw_answer, str):
        return ChatResponse(
            chat_id=chat_id,
            agent_used=agent_used,
            scene="main",
            answer_type="text",
            answer=raw_answer,
        )

    else:
        # Cas de fallback — utile si l'agent renvoie un type non reconnu
        return ChatResponse(
            chat_id=chat_id,
            agent_used=agent_used,
            scene="main",
            answer_type="text",
            answer=str(raw_answer),
        )
