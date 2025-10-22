from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    existing_user: bool
    user_id: str | None = None
    email: str | None = None
    given_name: str | None = None
    family_name: str | None = None


