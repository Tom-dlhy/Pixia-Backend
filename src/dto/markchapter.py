from pydantic import BaseModel

class MarkChapterRequest(BaseModel):
    chapter_id: str

class MarkChapterResponse(BaseModel):
    is_complete: bool

