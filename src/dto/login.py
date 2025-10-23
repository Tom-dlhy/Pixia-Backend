from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    existing_user: bool
    user_id: str | None = None
    email: str | None = None
    nom: str | None = None
    notion_token: str | None = None
    study: str | None = None

