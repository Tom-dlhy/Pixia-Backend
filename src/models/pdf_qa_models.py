from typing import Optional, List
from pydantic import BaseModel, Field


class EntreeQuestionPDF(BaseModel):
    """Entree du tool de Q&A sur un PDF unique."""
    session_id: str = Field("default", description="Identifiant de session")
    question: str = Field(..., description="Question utilisateur")
    file_uri: Optional[str] = Field(None, description="URI Gemini du fichier PDF a utiliser")
    top_k: int = Field(3, description="Nombre de passages a extraire (indicatif)")
    max_answer_words: int = Field(150, description="Longueur approximative de la reponse")


class Citation(BaseModel):
    page: Optional[int] = Field(None, description="Numero de page si identifiable")
    snippet: str = Field(..., description="Extrait brut pertinent")


class SortieQuestionPDF(BaseModel):
    ok: bool
    message: str
    answer: Optional[str] = None
    citations: Optional[List[Citation]] = None

