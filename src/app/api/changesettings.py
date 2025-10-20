from fastapi import APIRouter
from src.dto import ChangeSettingsRequest, ChangeSettingsResponse
from src.bdd import DBManager

router = APIRouter(prefix="/changesettings", tags=["ChangeSettings"])

@router.put("", response_model=ChangeSettingsResponse)
async def change_settings(req: ChangeSettingsRequest):
    db_manager = DBManager()
    await db_manager.change_settings(req.user_id, req.new_given_name, req.new_family_name, req.new_notion_url, req.new_drive_url)
    return ChangeSettingsResponse(user_id=req.user_id, is_changed=True)
