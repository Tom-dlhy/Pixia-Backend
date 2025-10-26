from fastapi import APIRouter, Form
from src.bdd import DBManager
from typing import Optional

router = APIRouter(prefix="/changesettings", tags=["ChangeSettings"])

@router.put("")
async def change_settings(
    user_id: str = Form(...),
    new_given_name: Optional[str] = Form(None),
    new_notion_token: Optional[str] = Form(None),
    new_niveau_etude: Optional[str] = Form(None),
):
    db_manager = DBManager()
    await db_manager.change_settings(
        user_id, 
        new_given_name, 
        new_niveau_etude, 
        new_notion_token
    )
    return {"user_id": user_id, "is_changed": True}

    