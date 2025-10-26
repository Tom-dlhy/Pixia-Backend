from pydantic import BaseModel

class CorrectPlainQuestionResponse(BaseModel):
    is_correct: bool