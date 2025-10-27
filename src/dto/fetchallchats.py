from pydantic import BaseModel
from typing import Optional, List, Literal, Union
from datetime import datetime
from src.models import ExerciseOutput
from sqlalchemy.sql.sqltypes import TIMESTAMP

class DisplaySessionsMain(BaseModel):
    session_id: str
    title: str
    update_time: datetime

class FetchAllChatsRequest(BaseModel):
    user_id: str

class FetchAllChatsResponse(BaseModel):
    sessions: List[DisplaySessionsMain] 
     # À adapter selon la structure des sessions renvoyées