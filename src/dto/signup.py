from pydantic import BaseModel

class SignupRequest(BaseModel):
    email: str
    password: str
    name: str | None = None

class SignupResponse(BaseModel):
    google_sub: str
    email: str | None = None
    name: str | None = None
    notion_token: str | None = None
    study: str | None = None
