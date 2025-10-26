"""
Gestionnaire centralisé des contextes de requête pour l'application.
Utilise ContextVar pour l'isolation thread-safe et async-safe des données de requête.
"""
from contextvars import ContextVar
from typing import Optional

# Context variables pour stocker les informations de la requête
_document_id_context: ContextVar[Optional[str]] = ContextVar('document_id', default=None)
_session_id_context: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
_user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_deep_course_id_context: ContextVar[Optional[str]] = ContextVar('deep_course_id', default=None)


# ===== SETTERS =====

def set_document_id(document_id: str) -> None:
    """Définit le document_id dans le contexte de la requête."""
    _document_id_context.set(document_id)


def set_session_id(session_id: str) -> None:
    """Définit le session_id dans le contexte de la requête."""
    _session_id_context.set(session_id)


def set_user_id(user_id: str) -> None:
    """Définit le user_id dans le contexte de la requête."""
    _user_id_context.set(user_id)


def set_deep_course_id(deep_course_id: str) -> None:
    """Définit le deep_course_id dans le contexte de la requête."""
    _deep_course_id_context.set(deep_course_id)


def set_request_context(
    document_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    deep_course_id: Optional[str] = None,
) -> None:
    """
    Définit tous les contextes de requête en une seule fois.
    Pratique pour initialiser le contexte au début d'une requête.
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
    """Récupère le document_id depuis le contexte de la requête."""
    return _document_id_context.get()


def get_session_id() -> Optional[str]:
    """Récupère le session_id depuis le contexte de la requête."""
    return _session_id_context.get()


def get_user_id() -> Optional[str]:
    """Récupère le user_id depuis le contexte de la requête."""
    return _user_id_context.get()


def get_deep_course_id() -> Optional[str]:
    """Récupère le deep_course_id depuis le contexte de la requête."""
    return _deep_course_id_context.get()


# ===== CLEANUP =====

def clear_request_context() -> None:
    """
    Nettoie tous les contextes de requête.
    Note: En pratique, Python nettoie automatiquement les ContextVar 
    à la fin de chaque tâche async, mais cette fonction peut être 
    utile pour les tests ou le debugging.
    """
    _document_id_context.set(None)
    _session_id_context.set(None)
    _user_id_context.set(None)
    _deep_course_id_context.set(None)
