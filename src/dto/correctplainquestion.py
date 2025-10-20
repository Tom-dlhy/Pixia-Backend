from pydantic import BaseModel

class CorrectPlainQuestionRequest(BaseModel):
    doc_id: str
    id_question: str
    answer: str
    question: str
    response: str

class CorrectPlainQuestionResponse(BaseModel):
    is_correct: bool

