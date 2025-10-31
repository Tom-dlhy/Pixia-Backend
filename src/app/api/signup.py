"""Signup endpoint for new user registration."""

import logging
from uuid import uuid4

from fastapi import APIRouter

from src.bdd import DBManager
from src.dto import SignupRequest, SignupResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/signup", tags=["Signup"])

@router.post("", response_model=SignupResponse)
async def signup(req: SignupRequest):
    db_manager = DBManager()
    google_sub = str(uuid4())
    user = await db_manager.signup_user(
        google_sub, req.email, req.name or "", notion_token="", study=""
    )
    
    # Validate user object was created
    if not user or not isinstance(user, dict):
        logger.error("Failed to create user during signup")
        raise ValueError("User registration failed")
    
    return SignupResponse(
        google_sub=user.get("google_sub", google_sub),
        email=user.get("email"),
        name=user.get("name"),
        notion_token=user.get("notion_token"),
        study=user.get("study"),
    )