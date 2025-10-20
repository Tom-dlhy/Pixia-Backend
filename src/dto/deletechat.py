from pydantic import BaseModel

class DeleteChatRequest(BaseModel):
    user_id: str
    session_id: str
