from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class DocumentInfo(BaseModel):
    doc_id: str
    session_id: str
    content: dict


class FetchChatRequest(BaseModel):
    user_id: str
    session_id: str


class EventMessage(BaseModel):
    type: Literal["user", "bot", "system", "unknown"]
    text: Optional[str] = None
    timestamp: Optional[datetime] = None


class FetchChatResponse(BaseModel):
    session_id: str
    user_id: str 
    messages: List[EventMessage]  
    
