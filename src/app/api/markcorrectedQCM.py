from fastapi import APIRouter
from src.dto import MarkIsCorrectedQCMRequest, MarkIsCorrectedQCMResponse
from src.bdd import DBManager

router = APIRouter(prefix="/markiscorrectedqcm", tags=["MarkIsCorrectedQCM"])

@router.put("", response_model=MarkIsCorrectedQCMResponse)
async def mark_iscorrected_qcm(req: MarkIsCorrectedQCMRequest):
    db_manager = DBManager()
    await db_manager.mark_is_corrected_qcm(req.doc_id, req.question_id)
    return MarkIsCorrectedQCMResponse(is_corrected=True)
