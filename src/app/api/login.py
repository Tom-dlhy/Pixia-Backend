from fastapi import APIRouter
from src.bdd import DBManager
from src.dto import LoginRequest, LoginResponse

router = APIRouter(prefix="/login", tags=["Login"])


@router.post("", response_model=LoginResponse)
async def login(req: LoginRequest):
    db_manager = DBManager()
    user = await db_manager.login_user(req.email)
    return LoginResponse(
        existing_user=bool(user),
        user_id=(user["google_sub"] if user else None),
        email=(user["email"] if user else None),
        given_name=(user["given_name"] if user else None),
        family_name=(user["family_name"] if user else None),
    )
