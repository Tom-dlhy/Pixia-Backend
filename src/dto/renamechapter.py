"""Rename chapter DTOs."""

from pydantic import BaseModel


class RenameChapterRequest(BaseModel):
    """Request to rename a chapter."""

    chapter_id: str
    title: str


class RenameChapterResponse(BaseModel):
    """Response after renaming a chapter."""

    chapter_id: str
    title: str