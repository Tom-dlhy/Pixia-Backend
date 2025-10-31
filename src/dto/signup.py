"""User registration DTOs."""

from typing import Optional

from pydantic import BaseModel


class SignupRequest(BaseModel):
    """Request for user registration."""

    email: str
    password: str
    name: Optional[str] = None


class SignupResponse(BaseModel):
    """Response after user registration."""

    google_sub: str
    email: Optional[str] = None
    name: Optional[str] = None
    notion_token: Optional[str] = None
    study: Optional[str] = None
