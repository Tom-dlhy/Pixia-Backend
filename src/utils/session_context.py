from typing import Dict, List

_SESSION_GEMINI_FILES: Dict[str, List[str]] = {}
_SESSION_GEMINI_FILE_NAMES: Dict[str, List[str]] = {}

def add_gemini_file(session_id: str, file_uri: str) -> None:
    files = _SESSION_GEMINI_FILES.setdefault(session_id, [])
    if file_uri not in files:
        files.append(file_uri)


def get_gemini_files(session_id: str) -> List[str]:
    return list(_SESSION_GEMINI_FILES.get(session_id, []))


def add_gemini_file_name(session_id: str, file_name: str) -> None:
    names = _SESSION_GEMINI_FILE_NAMES.setdefault(session_id, [])
    if file_name not in names:
        names.append(file_name)

def get_gemini_file_names(session_id: str) -> List[str]:
    return list(_SESSION_GEMINI_FILE_NAMES.get(session_id, []))

def clear_session(session_id: str) -> None:
    _SESSION_GEMINI_FILES.pop(session_id, None)
    _SESSION_GEMINI_FILE_NAMES.pop(session_id, None)
