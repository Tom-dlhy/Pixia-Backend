from fastapi import APIRouter
from src.dto import RenameChatRequest, RenameChatResponse
from src.bdd import DBManager

router = APIRouter(prefix="/renamechat", tags=["RenameChat"])

@router.put("", response_model=RenameChatResponse)
async def rename_chat(req: RenameChatRequest):
    db_manager = DBManager()
    await db_manager.rename_chat(req.session_id, req.title)
    return RenameChatResponse(session_id=req.session_id, title=req.title)
