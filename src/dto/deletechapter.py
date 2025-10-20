from pydantic import BaseModel

class DeleteChapterRequest(BaseModel):
    user_id: str
    chapter_id: str
