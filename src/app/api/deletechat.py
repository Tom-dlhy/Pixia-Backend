from fastapi import APIRouter, status
from src.dto import DeleteChatRequest
from src.bdd import DBManager

router = APIRouter(prefix="/deletechat", tags=["DeleteChat"])

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(req: DeleteChatRequest):
    db_manager = DBManager()
    await db_manager.delete_chat(req.session_id)
    return status.HTTP_204_NO_CONTENT
