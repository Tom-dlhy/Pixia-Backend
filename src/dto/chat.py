"""Chat response DTOs."""

from typing import Literal, Optional, Union

from pydantic import BaseModel


class AgentAnswer(BaseModel):
    """Raw agent response before final formatting."""

    type: Literal["text", "json", "speech"]
    content: Union[str, dict]


class ChatResponse(BaseModel):
    """Main response returned to frontend after agent processing."""

    session_id: str
    answer: str
    agent: Optional[str] = None
    redirect_id: Optional[str] = None
