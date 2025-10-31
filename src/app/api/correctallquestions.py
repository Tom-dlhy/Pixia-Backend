"""Endpoint to correct multiple plain text questions."""

from fastapi import APIRouter

from src.dto import CorrectMultipleQuestionsRequest, CorrectPlainQuestionResponse
from src.utils import agent_correct_plain_question

router = APIRouter(prefix="/correctallquestions", tags=["CorrectAllQuestions"])


@router.post("", response_model=list[CorrectPlainQuestionResponse])
async def correct_multiple_plain_questions(request: CorrectMultipleQuestionsRequest):
    """Evaluate multiple user answers and return correctness for each."""
    results = []
    for q in request.questions:
        is_correct = await agent_correct_plain_question(
            answer=q.user_answer,
            question=q.question,
            response=q.expected_answer
        )
        results.append(CorrectPlainQuestionResponse(is_correct=is_correct))
    
    return results