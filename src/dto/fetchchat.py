from pydantic import BaseModel
from typing import Optional, List, Literal, Union
from datetime import datetime
from src.models import ExerciseOutput
from sqlalchemy.sql.sqltypes import TIMESTAMP

class document(BaseModel):
    doc_id: str
    session_id: str
    content: dict


class FetchChatRequest(BaseModel):
    user_id: str
    session_id: str

class FetchAllChatsResponse(BaseModel):
    session_id: str
    title: str
    state: 
    events:
    scene:
    document: List[document]