"""Data Transfer Objects (DTOs) for API request/response validation.

This package provides Pydantic models for type-safe API contracts.
DTOs ensure strong typing and automatic validation of all API inputs/outputs.
"""

from .chat import ChatResponse, AgentAnswer
from .correctplainquestion import (
    CorrectMultipleQuestionsRequest,
    CorrectPlainQuestionResponse,
    CorrectQuestionRequest,
)
from .deletechapter import DeleteChapterRequest
from .deletechat import DeleteChatRequest
from .fetchallchats import (
    DisplaySessionsMain,
    FetchAllChatsRequest,
    FetchAllChatsResponse,
)
from .fetchchat import EventMessage, FetchChatRequest, FetchChatResponse
from .fetchexercise import FetchExerciseResponse
from .login import LoginRequest, LoginResponse
from .markchapter import MarkChapterRequest, MarkChapterResponse
from .markcorrectedQCM import MarkIsCorrectedQCMRequest, MarkIsCorrectedQCMResponse
from .renamechapter import RenameChapterRequest, RenameChapterResponse
from .renamechat import RenameChatRequest, RenameChatResponse
from .signup import SignupRequest, SignupResponse

__all__ = [
    "ChatResponse",
    "AgentAnswer",
    "CorrectMultipleQuestionsRequest",
    "CorrectPlainQuestionResponse",
    "CorrectQuestionRequest",
    "DeleteChapterRequest",
    "DeleteChatRequest",
    "DisplaySessionsMain",
    "EventMessage",
    "FetchAllChatsRequest",
    "FetchAllChatsResponse",
    "FetchChatRequest",
    "FetchChatResponse",
    "FetchExerciseResponse",
    "LoginRequest",
    "LoginResponse",
    "MarkChapterRequest",
    "MarkChapterResponse",
    "MarkIsCorrectedQCMRequest",
    "MarkIsCorrectedQCMResponse",
    "RenameChapterRequest",
    "RenameChapterResponse",
    "RenameChatRequest",
    "RenameChatResponse",
    "SignupRequest",
    "SignupResponse",
]