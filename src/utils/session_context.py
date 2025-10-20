from typing import Dict, List

# Stockage en mémoire des fichiers Gemini associés à une session.
_SESSION_GEMINI_FILES: Dict[str, List[str]] = {}


def add_gemini_file(session_id: str, file_id: str) -> None:
    files = _SESSION_GEMINI_FILES.setdefault(session_id, [])
    if file_id not in files:
        files.append(file_id)


def get_gemini_files(session_id: str) -> List[str]:
    return list(_SESSION_GEMINI_FILES.get(session_id, []))


def clear_session(session_id: str) -> None:
    _SESSION_GEMINI_FILES.pop(session_id, None)

