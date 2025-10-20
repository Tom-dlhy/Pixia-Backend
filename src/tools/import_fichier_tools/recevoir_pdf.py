from typing import Dict, Any
import os
import logging

from src.models.import_fichier_model import EntreeRecevoirEtLirePDF, SortieRecevoirEtLirePDF
from src.utils import gemini_upload_file, add_gemini_file

logger = logging.getLogger(__name__)


def recevoir_et_lire_pdf(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reçoit un PDF par chemin local et l'upload vers Gemini, puis l'ajoute au contexte de la session.
    - Pas de base64 ni de stockage persistant.
    - Répond toujours avec un dict {ok, message, ...}.
    """
    try:
        data = EntreeRecevoirEtLirePDF(**payload)

        # Chemin obligatoire et validation minimale
        chemin_source = data.file_path
        if not chemin_source or not os.path.exists(chemin_source):
            return SortieRecevoirEtLirePDF(ok=False, message="Fichier introuvable ou chemin invalide").model_dump()
        if not chemin_source.lower().endswith(".pdf"):
            return SortieRecevoirEtLirePDF(ok=False, message="Le fichier doit être un PDF").model_dump()

        # Upload vers Gemini
        uploaded_file = gemini_upload_file(chemin_source)  # type: ignore
        file_id = getattr(uploaded_file, "name", None)
        file_state = getattr(uploaded_file, "state", None)

        if file_id:
            add_gemini_file(data.session_id, file_id)

        return SortieRecevoirEtLirePDF(
            ok=True,
            message="PDF uploadé vers Gemini et ajouté au contexte de session.",
            nom_effectif=os.path.basename(chemin_source),
            gemini_file_id=file_id,
            gemini_state=file_state,
        ).model_dump()
    except Exception as e:
        return SortieRecevoirEtLirePDF(ok=False, message=f"Erreur inattendue : {e}").model_dump()


def tool_spec_recevoir_et_lire_pdf() -> dict:
    """Spécification pour enregistrement dans les agents ADK."""
    return {
        "name": "recevoir_et_lire_pdf",
        "description": (
            "Reçoit un PDF via chemin local et l'upload vers Gemini pour contexte."
        ),
        "input_schema": EntreeRecevoirEtLirePDF.model_json_schema(),
        "output_schema": SortieRecevoirEtLirePDF.model_json_schema(),
        "handler": recevoir_et_lire_pdf,
    }

