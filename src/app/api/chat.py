from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    user_id: str
    message: str
    chat_id: Optional[str] = None

class ChatResponse(BaseModel):
    chat_id: str
    answer: str
    agent_used: str = "echo"

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Echo minimal pour valider le pipeline
    chat_id = req.chat_id or "demo-chat"
    return ChatResponse(chat_id=chat_id, answer=f"Tu as dit: {req.message}")
