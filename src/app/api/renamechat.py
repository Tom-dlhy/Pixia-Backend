"""Endpoint to rename a chat session."""

from fastapi import APIRouter

from src.bdd import DBManager
from src.dto import RenameChatRequest, RenameChatResponse

router = APIRouter(prefix="/renamechat", tags=["RenameChat"])


@router.put("", response_model=RenameChatResponse)
async def rename_chat(req: RenameChatRequest):
    """Rename a chat session."""
    db_manager = DBManager()
    # await db_manager.rename_chat(req.session_id, req.title) # TODO
    return RenameChatResponse(session_id=req.session_id, title=req.title)
