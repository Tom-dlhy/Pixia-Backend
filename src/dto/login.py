"""Login DTOs."""

from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Request for user authentication."""

    email: str
    password: str


class LoginResponse(BaseModel):
    """Response after user authentication."""

    existing_user: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    nom: Optional[str] = None
    notion_token: Optional[str] = None
    study: Optional[str] = None

