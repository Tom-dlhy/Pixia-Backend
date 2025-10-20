from fastapi import APIRouter
from src.dto import CorrectPlainQuestionRequest, CorrectPlainQuestionResponse
from src.bdd import DBManager
from src.utils import agent_correct_plain_question

router = APIRouter(prefix="/correctplainquestion", tags=["CorrectPlainQuestion"])

@router.post("", response_model=CorrectPlainQuestionResponse)
async def correct_plain_question(req: CorrectPlainQuestionRequest):
    db_manager = DBManager()
    doc_id = req.doc_id
    id_question = req.id_question
    
    is_correct = await agent_correct_plain_question(
        answer=req.answer,
        question=req.question,
        response=req.response
    )

    await db_manager.correct_plain_question(doc_id, id_question, is_correct, req.answer)
    
    return CorrectPlainQuestionResponse(is_correct=is_correct)


 

