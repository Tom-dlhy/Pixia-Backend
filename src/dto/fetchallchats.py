from pydantic import BaseModel
from typing import List
from datetime import datetime


class DisplaySessionsMain(BaseModel):
    session_id: str
    title: str
    update_time: datetime

class FetchAllChatsRequest(BaseModel):
    user_id: str

class FetchAllChatsResponse(BaseModel):
    sessions: List[DisplaySessionsMain] 
