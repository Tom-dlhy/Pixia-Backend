from pydantic import BaseModel

class RenameChatRequest(BaseModel):
    session_id: str
    title: str

class RenameChatResponse(BaseModel):
    session_id: str
    title: str