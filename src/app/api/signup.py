from fastapi import APIRouter
from src.bdd import DBManager
from src.dto import SignupRequest, SignupResponse
from uuid import uuid4

router = APIRouter(prefix="/signup", tags=["Signup"])

@router.post("", response_model=SignupResponse)
async def signup(req: SignupRequest):
    db_manager = DBManager()
    google_sub = str(uuid4())
    user = await db_manager.signup_user(
        google_sub, req.email, req.name or "", notion_token="", study=""
    )
    return SignupResponse(
        google_sub=user["google_sub"],
        email=user["email"],
        name=user["name"],
        notion_token=user["notion_token"],
        study=user["study"],
    )