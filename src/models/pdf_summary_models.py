from typing import Optional, List
from pydantic import BaseModel, Field


class EntreeResumerPDFs(BaseModel):
    session_id: str = Field("default", description="Identifiant unique de la session utilisateur")
    file_ids: Optional[List[str]] = Field(None, description="Liste d'IDs Gemini de fichiers à résumer (facultatif)")
    max_words: int = Field(250, description="Longueur cible du résumé en nombre de mots")


class SortieResumerPDFs(BaseModel):
    ok: bool
    message: str
    summary: Optional[str] = None

