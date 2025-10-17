# src/prompt_builders.py
from typing import Any, Optional
import json
from src.prompts import AGENT_PROMPT_NORMAL_AGENT

def construire_prompt_systeme_agent_normal(
    sujet: Optional[str] = None,
    niveau: Optional[str] = None,
    objectifs: Optional[list[str]] = None,
    contexte_libre: Optional[dict[str, Any]] = None,
) -> str:
    """
    Construit un prompt système pour l'agent Normal en injectant un contexte léger.
    Tous les champs sont optionnels.
    """
    contexte: dict[str, Any] = {}
    if sujet:
        contexte["sujet"] = sujet
    if niveau:
        contexte["niveau"] = niveau
    if objectifs:
        contexte["objectifs"] = objectifs
    if contexte_libre:
        contexte["contexte_libre"] = contexte_libre

    bloc_contexte = ""
    if contexte:
        bloc_contexte = "\n\nContexte fourni par l'orchestrateur :\n" + json.dumps(
            contexte, ensure_ascii=False, indent=2
        )

    return f"{AGENT_PROMPT_NORMAL_AGENT}{bloc_contexte}"
