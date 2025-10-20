from pydantic import BaseModel

class RenameChapterRequest(BaseModel):
    chapter_id: str
    title: str

class RenameChapterResponse(BaseModel):
    chapter_id: str
    title: str