from pydantic import BaseModel
from typing import Optional, Literal, Union

class LoadFile(BaseModel):
    filename: str
    size: int
    content_type: str

class AgentAnswer(BaseModel):
    """Représente la réponse brute de l'agent avant formatage final."""

    type: Literal["text", "json", "speech"]
    content: Union[str, dict]

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    agent: Optional[str] = None
    redirect_id: Optional[str] = None
