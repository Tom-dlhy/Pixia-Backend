"""Mark chapter completion DTOs."""

from pydantic import BaseModel


class MarkChapterRequest(BaseModel):
    """Request to mark a chapter as complete."""

    chapter_id: str


class MarkChapterResponse(BaseModel):
    """Response indicating chapter completion status."""

    is_complete: bool

