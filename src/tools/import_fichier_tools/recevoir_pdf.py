from __future__ import annotations
import os
from typing import Dict, Any
from src.models.import_fichier_model import EntreeRecevoirPDF, SortieRecevoirPDF
from src.utils.import_fichier import (
    is_pdf_ext, is_pdf_content_type, starts_with_pdf_magic,
    sha256_hex, count_pages, ensure_dir, sanitize_filename,
    decode_b64_to_bytes, write_unique
)

DEFAULT_UPLOAD_DIR = os.getenv("PDF_UPLOAD_DIR", "data/uploads")

def recevoir_pdf(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 1) Validation d’entrée (Pydantic)
    data = EntreeRecevoirPDF(**payload)

    # 2) Décodage base64 + limite taille
    ok, contenu, msg = decode_b64_to_bytes(data.contenu_base64, size_limit_mib=50)
    if not ok:
        return SortieRecevoirPDF(ok=False, message=msg).model_dump()

    # 3) Nom de fichier + extension
    nom = sanitize_filename(data.nom_fichier or "document.pdf")
    if not is_pdf_ext(nom):
        # force l’extension .pdf si l’utilisateur envoie un nom sans .pdf
        nom = f"{nom}.pdf"

    # 4) Content-Type (facultatif mais vérifié si fourni)
    if data.content_type is not None and not is_pdf_content_type(data.content_type):
        return SortieRecevoirPDF(ok=False, message=f"Content-Type invalide: {data.content_type}").model_dump()

    # 5) Signature binaire + lecture PDF (si dispo)
    if not starts_with_pdf_magic(contenu):
        return SortieRecevoirPDF(ok=False, message="Signature binaire non PDF (%PDF- absent)").model_dump()

    # 6) Écriture disque (anti-collision)
    chemin = write_unique(DEFAULT_UPLOAD_DIR, nom, contenu)

    # 7) Métadonnées
    pages = count_pages(contenu)  # None si pypdf absent ou illisible
    digest = sha256_hex(contenu)

    return SortieRecevoirPDF(
        ok=True,
        message="PDF reçu et stocké",
        chemin_local=chemin,
        sha256=digest,
        pages=pages,
        nom_effectif=os.path.basename(chemin),
    ).model_dump()

def tool_spec_recevoir_pdf() -> dict:
    return {
        "name": "recevoir_pdf",
        "description": "Reçoit un PDF (base64), le valide et le stocke localement.",
        "input_schema": EntreeRecevoirPDF.model_json_schema(),
        "output_schema": SortieRecevoirPDF.model_json_schema(),
        "handler": recevoir_pdf,
    }