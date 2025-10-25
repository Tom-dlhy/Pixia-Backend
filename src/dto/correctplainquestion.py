from pydantic import BaseModel
from typing import Optional


class CorrectPlainQuestionRequest(BaseModel):
    question: str
    user_answer: str
    expected_answer: str
    doc_id: Optional[str] = None
    id_question: Optional[str] = None


class CorrectPlainQuestionResponse(BaseModel):
    is_correct: bool
    feedback: Optional[str] = None
