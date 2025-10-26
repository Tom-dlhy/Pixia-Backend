from pydantic import BaseModel
from typing import Optional

class FetchExerciseResponse(BaseModel):
    session_id: str
    answer: str
    agent: Optional[str] = None
    redirect_id: Optional[str] = None
