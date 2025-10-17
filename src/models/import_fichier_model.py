
from typing import Optional, List
from pydantic import BaseModel, Field

class EntreeRecevoirEtLirePDF(BaseModel):
    """Entrée pour le tool 'recevoir_et_lire_pdf'."""
    nom_fichier: str = Field(..., description="Nom du fichier (terminé par .pdf)")
    contenu_base64: str = Field(..., description="Contenu du fichier PDF encodé en base64")
    content_type: Optional[str] = Field(None, description="Type MIME du fichier (ex: application/pdf)")
    session_id: str = Field("default", description="Identifiant unique de la session utilisateur")
    max_chars_per_chunk: int = Field(6000, description="Taille max d'un chunk de texte (caractères)")
    max_chunks: int = Field(5, description="Nombre maximum de chunks retournés")

class SortieRecevoirEtLirePDF(BaseModel):
    """Sortie du tool 'recevoir_et_lire_pdf'."""
    ok: bool
    message: str
    chemin_pdf: Optional[str] = None
    chemin_txt: Optional[str] = None
    pages: Optional[int] = None
    sha256: Optional[str] = None
    chunks: Optional[List[str]] = None
    total_chars: Optional[int] = None
    nom_effectif: Optional[str] = None
