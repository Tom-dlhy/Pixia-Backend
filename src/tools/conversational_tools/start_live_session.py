import os, requests
from typing import Optional, Dict, Any

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def start_live_session(
    topic: str,
    language: str = "fr-FR",
    context_summary: Optional[str] = None
) -> Dict[str, Any]:
    """Crée la session live et renvoie {session_id, ws_url} (chemin FastAPI)."""
    r = requests.post(f"{BACKEND_URL}/live/start", json={
        "topic": topic, "language": language, "context_summary": context_summary
    }, timeout=8)
    r.raise_for_status()
    return r.json()
