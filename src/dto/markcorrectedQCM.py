from pydantic import BaseModel

class MarkIsCorrectedQCMRequest(BaseModel):
    doc_id: str
    question_id: str

class MarkIsCorrectedQCMResponse(BaseModel):
    is_corrected: bool

