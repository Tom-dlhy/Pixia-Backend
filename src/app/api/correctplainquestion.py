from fastapi import APIRouter, Form
from src.dto import CorrectPlainQuestionResponse
from src.utils import agent_correct_plain_question

router = APIRouter(prefix="/correctplainquestion", tags=["CorrectPlainQuestion"])


@router.post("", response_model=CorrectPlainQuestionResponse)
async def correct_plain_question(
    question: str = Form(...),
    user_answer: str = Form(...),
    expected_answer: str = Form(...),
):
    is_correct = await agent_correct_plain_question(
        answer=user_answer, question=question, response=expected_answer
    )

    return CorrectPlainQuestionResponse(is_correct=is_correct)
