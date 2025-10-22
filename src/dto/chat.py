from pydantic import BaseModel
from typing import Optional, List, Literal, Union
from src.models import ExerciseOutput, CourseOutput, DeepCourseOutput

class LoadFile(BaseModel):
    filename: str
    size: int
    content_type: str


from pydantic import BaseModel
from typing import Literal, Union
from src.models import ExerciseOutput, CourseOutput, DeepCourseOutput


# ---- 1️⃣ Représente une réponse de l'agent ----
class AgentAnswer(BaseModel):
    """Représente la réponse brute de l'agent avant formatage final."""

    type: Literal["text", "json", "speech"]
    content: Union[str, dict]


# ---- 2️⃣ Structure principale renvoyée au frontend ----
class ChatResponse(BaseModel):
    session_id: str
    answer: str
    agent: Optional[str] = None
    redirect_id: Optional[str] = None
