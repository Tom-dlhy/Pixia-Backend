"""Endpoint to correct a plain text question."""

from fastapi import APIRouter

from src.dto import CorrectPlainQuestionResponse, CorrectQuestionRequest
from src.utils import agent_correct_plain_question

router = APIRouter(prefix="/correctplainquestion", tags=["CorrectPlainQuestion"])


@router.post("", response_model=CorrectPlainQuestionResponse)
async def correct_plain_question(request: CorrectQuestionRequest):
    """Evaluate if a user's answer is correct."""
    is_correct = await agent_correct_plain_question(
        answer=request.user_answer, question=request.question, response=request.expected_answer
    )
    return CorrectPlainQuestionResponse(is_correct=is_correct)
