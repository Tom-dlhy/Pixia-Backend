from pydantic import BaseModel
from typing import Optional, List, Literal, Union
from datetime import datetime
from src.models import ExerciseOutput
from sqlalchemy.sql.sqltypes import TIMESTAMP


class DocumentInfo(BaseModel):
    doc_id: str
    session_id: str
    content: dict


class FetchChatRequest(BaseModel):
    user_id: str
    session_id: str


class FetchChatResponse(BaseModel):
    session_id: str
    title: Optional[str] = None
    state: Optional[str] = None
    events: Optional[List[dict]] = None
    scene: Optional[str] = None
    document: Optional[List[DocumentInfo]] = None


class EventMessage(BaseModel):
    type: Literal["user", "bot", "system", "unknown"]
    text: Optional[str] = None
    timestamp: Optional[datetime] = None
