from pydantic import BaseModel
from typing import Optional

class ChangeSettingsRequest(BaseModel):
    user_id: str
    new_given_name: Optional[str] = None
    new_family_name: Optional[str] = None
    new_notion_url: Optional[str] = None
    new_drive_url: Optional[str] = None

class ChangeSettingsResponse(BaseModel):
    user_id: str
    is_changed: bool

