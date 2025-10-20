from fastapi import APIRouter
from src.bdd import DBManager
from src.dto import SignupRequest, SignupResponse
from uuid import uuid4

router = APIRouter(prefix="/signup", tags=["Signup"])

#     async def signup_user(self, google_sub: str, email: str, given_name: str = "", family_name: str = ""):

@router.post("", response_model=SignupResponse)
async def signup(req: SignupRequest):
    db_manager = DBManager()
    google_sub = str(uuid4())
    user = await db_manager.signup_user(google_sub, req.email, req.given_name, req.family_name)
    return SignupResponse(
        google_sub=user["google_sub"],
        email=user["email"],
        given_name=user["given_name"],
        family_name=user["family_name"],
    )
