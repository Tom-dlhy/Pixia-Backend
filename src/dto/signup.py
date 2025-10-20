from pydantic import BaseModel

class SignupRequest(BaseModel):
    email: str
    password: str
    given_name: str
    family_name: str

class SignupResponse(BaseModel):
    google_sub: str
    email: str | None = None
    given_name: str | None = None
    family_name: str | None = None

