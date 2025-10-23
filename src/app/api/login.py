from fastapi import APIRouter
from src.bdd import DBManager
from src.dto import LoginRequest, LoginResponse
from logging import getLogger
logger = getLogger(__name__)

router = APIRouter(prefix="/login", tags=["Login"])

@router.post("", response_model=LoginResponse)
async def login(req: LoginRequest):
    db_manager = DBManager()
    user = await db_manager.login_user(req.email)

    logger.info(f"id: {user['google_sub'] if user else 'N/A'}, email: {user['email'] if user else 'N/A'} logged in.")

    notion_token = "fake_notion_token_12345"  # Placeholder for actual token retrieval logic

    study = "Master 2 de Fortnite"

    return LoginResponse(
        existing_user=bool(user),
        user_id=(user["google_sub"] if user else None),  
        email=(user["email"] if user else None),
        nom=(user["given_name"] if user else None),
        notion_token=notion_token,
        study=study,
    )
