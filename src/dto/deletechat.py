from pydantic import BaseModel

class DeleteChatRequest(BaseModel):
    session_id: str
