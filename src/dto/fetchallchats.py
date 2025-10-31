"""Fetch all chat sessions DTOs."""

from datetime import datetime
from typing import List

from pydantic import BaseModel


class DisplaySessionsMain(BaseModel):
    """Summary of a chat session for display."""

    session_id: str
    title: str
    update_time: datetime


class FetchAllChatsRequest(BaseModel):
    """Request to fetch all chat sessions for a user."""

    user_id: str


class FetchAllChatsResponse(BaseModel):
    """Response containing all chat sessions for a user."""

    sessions: List[DisplaySessionsMain]