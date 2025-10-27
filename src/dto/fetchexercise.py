from pydantic import BaseModel
from typing import Optional, List, Literal, Union
from src.models import ExerciseOutput, CourseOutput, DeepCourseOutput


# ---- 2️⃣ Structure principale renvoyée au frontend ----
class FetchExerciseResponse(BaseModel):
    session_id: str
    answer: str
    agent: Optional[str] = None
    redirect_id: Optional[str] = None
