from pydantic import BaseModel, Field
from typing import Optional


class EntreeRecevoirPDF(BaseModel):
    """Entrée standardisée pour l’outil de réception PDF."""
    nom_fichier: str = Field(..., description="Nom terminé par .pdf")
    contenu_base64: str = Field(..., description="Contenu encodé en base64")
    content_type: Optional[str] = Field(None, description="application/pdf")


class SortieRecevoirPDF(BaseModel):
    """Sortie normalisée de l’outil (succès/erreur + métadonnées)."""
    ok: bool
    message: str
    chemin_local: Optional[str] = None
    sha256: Optional[str] = None
    pages: Optional[int] = None
    nom_effectif: Optional[str] = None
