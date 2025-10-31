"""Tool output models."""

from typing import Optional

from pydantic import BaseModel


class GenerativeToolOutput(BaseModel):
    """Output from a generative tool."""

    agent: Optional[str]
    redirect_id: Optional[str]
    completed: bool