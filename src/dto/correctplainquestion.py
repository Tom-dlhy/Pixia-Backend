"""Question correction DTOs."""

from typing import List

from pydantic import BaseModel


class CorrectPlainQuestionResponse(BaseModel):
    """Response indicating if a question answer is correct."""

    is_correct: bool


class CorrectQuestionRequest(BaseModel):
    """Request to correct a single question."""

    question: str
    user_answer: str
    expected_answer: str


class CorrectMultipleQuestionsRequest(BaseModel):
    """Request to correct multiple questions."""

    questions: List[CorrectQuestionRequest]
