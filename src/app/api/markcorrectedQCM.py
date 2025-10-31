"""Endpoint to mark a QCM question as corrected."""

from fastapi import APIRouter

from src.bdd import DBManager
from src.dto import MarkIsCorrectedQCMRequest, MarkIsCorrectedQCMResponse

router = APIRouter(prefix="/markiscorrectedqcm", tags=["MarkIsCorrectedQCM"])


@router.put("", response_model=MarkIsCorrectedQCMResponse)
async def mark_iscorrected_qcm(req: MarkIsCorrectedQCMRequest):
    """Mark a QCM question as corrected."""
    db_manager = DBManager()
    await db_manager.mark_is_corrected_qcm(req.doc_id, req.question_id)
    return MarkIsCorrectedQCMResponse(is_corrected=True)
