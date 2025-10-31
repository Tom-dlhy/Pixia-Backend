"""Delete chat session DTOs."""

from pydantic import BaseModel


class DeleteChatRequest(BaseModel):
    """Request to delete a chat session."""

    user_id: str
    session_id: str
