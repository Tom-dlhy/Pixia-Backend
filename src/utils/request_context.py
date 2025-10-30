"""
Centralized request context management.

Uses ContextVar for thread-safe and async-safe request data isolation.
Enables access to request-scoped variables across the application without
passing them through function parameters.
It is used especially to pass vars to tools used by the agents.
"""

from contextvars import ContextVar
from typing import Optional

# Request context variables
_document_id_context: ContextVar[Optional[str]] = ContextVar('document_id', default=None)
_session_id_context: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
_user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_deep_course_id_context: ContextVar[Optional[str]] = ContextVar('deep_course_id', default=None)


# ===== SETTERS =====


def set_document_id(document_id: str) -> None:
    """Set document_id in request context."""
    _document_id_context.set(document_id)


def set_session_id(session_id: str) -> None:
    """Set session_id in request context."""
    _session_id_context.set(session_id)


def set_user_id(user_id: str) -> None:
    """Set user_id in request context."""
    _user_id_context.set(user_id)


def set_deep_course_id(deep_course_id: str) -> None:
    """Set deep_course_id in request context."""
    _deep_course_id_context.set(deep_course_id)


def set_request_context(
    document_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    deep_course_id: Optional[str] = None,
) -> None:
    """
    Set all request context variables at once.

    Convenience function to initialize context at request start.

    Args:
        document_id: Document identifier
        session_id: Session identifier
        user_id: User identifier
        deep_course_id: Deep course identifier
    """
    if document_id:
        set_document_id(document_id)
    if session_id:
        set_session_id(session_id)
    if user_id:
        set_user_id(user_id)
    if deep_course_id:
        set_deep_course_id(deep_course_id)


# ===== GETTERS =====


def get_document_id() -> Optional[str]:
    """Get document_id from request context."""
    return _document_id_context.get()


def get_session_id() -> Optional[str]:
    """Get session_id from request context."""
    return _session_id_context.get()


def get_user_id() -> Optional[str]:
    """Get user_id from request context."""
    return _user_id_context.get()


def get_deep_course_id() -> Optional[str]:
    """Get deep_course_id from request context."""
    return _deep_course_id_context.get()


# ===== CLEANUP =====


def clear_request_context() -> None:
    """
    Clear all request context variables.

    Note: Python automatically cleans up ContextVar at the end of each async task,
    but this function is useful for manual cleanup in tests or debugging scenarios.
    """
    _document_id_context.set(None)
    _session_id_context.set(None)
    _user_id_context.set(None)
    _deep_course_id_context.set(None)

