from pydantic import BaseModel
from typing import Optional

class GenerativeToolOutput(BaseModel):
    agent: Optional[str]
    redirect_id: Optional[str]
    completed: bool