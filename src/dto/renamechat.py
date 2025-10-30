"""Rename chat session DTOs."""

from pydantic import BaseModel


class RenameChatRequest(BaseModel):
    """Request to rename a chat session."""

    session_id: str
    title: str


class RenameChatResponse(BaseModel):
    """Response after renaming a chat session."""

    session_id: str
    title: str