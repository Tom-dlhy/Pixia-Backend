"""Delete chapter DTOs."""

from pydantic import BaseModel


class DeleteChapterRequest(BaseModel):
    """Request to delete a chapter."""

    user_id: str
    chapter_id: str
