from pydantic import BaseModel
from typing import List

class CorrectPlainQuestionResponse(BaseModel):
    is_correct: bool

class CorrectQuestionRequest(BaseModel):
    question: str
    user_answer: str
    expected_answer: str

class CorrectMultipleQuestionsRequest(BaseModel):
    questions: List[CorrectQuestionRequest]
