"""Fetch specific chat session DTOs."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class DocumentInfo(BaseModel):
    """Information about a document in a chat session."""

    doc_id: str
    session_id: str
    content: dict


class FetchChatRequest(BaseModel):
    """Request to fetch a specific chat session."""

    user_id: str
    session_id: str


class EventMessage(BaseModel):
    """Message event in a chat session."""

    type: Literal["user", "bot", "system", "unknown"]
    text: Optional[str] = None
    timestamp: Optional[datetime] = None


class FetchChatResponse(BaseModel):
    """Response containing a specific chat session with all messages."""

    session_id: Optional[str]
    user_id: str
    messages: List[EventMessage]  
    
