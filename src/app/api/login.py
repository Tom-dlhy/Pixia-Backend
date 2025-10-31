"""Login endpoint for user authentication."""

from logging import getLogger

from fastapi import APIRouter

from src.bdd import DBManager
from src.dto import LoginRequest, LoginResponse

logger = getLogger(__name__)

router = APIRouter(prefix="/login", tags=["Login"])

@router.post("", response_model=LoginResponse)
async def login(req: LoginRequest):
    db_manager = DBManager()
    user = await db_manager.login_user(req.email)

    logger.info(f"id: {user['google_sub'] if user else 'N/A'}, email: {user['email'] if user else 'N/A'} logged in.")

    return LoginResponse(
        existing_user=bool(user),
        user_id=(user["google_sub"] if user else None),  
        email=(user["email"] if user else None),
        nom=(user["name"] if user else None),
        notion_token=(user["notion_token"] if user else None),
        study=(user["study"] if user else None),
    )
