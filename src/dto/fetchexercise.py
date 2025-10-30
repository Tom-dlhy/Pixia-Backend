"""Fetch exercise response DTO."""

from typing import Optional

from pydantic import BaseModel


class FetchExerciseResponse(BaseModel):
    """Response returned after fetching exercise from agent."""

    session_id: str
    answer: str
    agent: Optional[str] = None
    redirect_id: Optional[str] = None
