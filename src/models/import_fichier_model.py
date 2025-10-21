from typing import Optional
from pydantic import BaseModel, Field


class EntreeRecevoirEtLirePDF(BaseModel):
    """Entrée pour le tool 'recevoir_et_lire_pdf' (simplifié: chemin de fichier uniquement)."""
    file_path: str = Field(..., description="Chemin local du fichier PDF à uploader vers Gemini")
    session_id: str = Field("default", description="Identifiant unique de la session utilisateur")


class SortieRecevoirEtLirePDF(BaseModel):
    """Sortie du tool 'recevoir_et_lire_pdf' (simplifiée)."""
    ok: bool
    message: str
    nom_effectif: Optional[str] = None
    gemini_file_id: Optional[str] = Field(None, description="Identifiant du fichier côté Gemini (resource name)")
    gemini_state: Optional[str] = Field(None, description="État de traitement du fichier côté Gemini")

