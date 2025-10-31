"""Mark QCM question as corrected DTOs."""

from pydantic import BaseModel


class MarkIsCorrectedQCMRequest(BaseModel):
    """Request to mark a QCM question as corrected."""

    doc_id: str
    question_id: str


class MarkIsCorrectedQCMResponse(BaseModel):
    """Response indicating QCM correction status."""

    is_corrected: bool

