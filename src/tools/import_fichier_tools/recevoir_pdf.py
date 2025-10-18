from typing import Dict, Any
import os

from src.models.import_fichier_model import EntreeRecevoirEtLirePDF, SortieRecevoirEtLirePDF
from src.utils import (
    is_pdf_ext, is_pdf_content_type, starts_with_pdf_magic,
    sha256_hex, decode_b64_to_bytes, write_unique, count_pages,
    extract_text_from_pdf_bytes, chunk_text, sanitize_filename,
    session_upload_dir, session_text_dir
)



def recevoir_et_lire_pdf(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reçoit un PDF (base64), le valide, le stocke dans la session, extrait le texte et renvoie un résumé.
    - Rejette proprement tout fichier non-PDF (PowerPoint & co.) sans rien écrire.
    - Écrit sur disque uniquement après validation PDF.
    - Ne lève jamais d'exception vers ADK (toujours un dict {ok, message, ...}).
    """
    try:
        # 0) Validation d'entrée (Pydantic)
        data = EntreeRecevoirEtLirePDF(**payload)

        # 1) Décodage Base64 + limite taille (AUCUNE écriture disque avant validation PDF)
        ok, contenu, msg = decode_b64_to_bytes(data.contenu_base64, size_limit_mib=50)
        if not ok:
            return SortieRecevoirEtLirePDF(ok=False, message=msg).model_dump()

        # 2) Rejet immédiat si content-type explicite et non-PDF (pas d'I/O)
        if data.content_type is not None and not is_pdf_content_type(data.content_type):
            return SortieRecevoirEtLirePDF(
                ok=False, message=f"Fichier refusé : Content-Type non PDF ({data.content_type})."
            ).model_dump()

        # 3) Vérification signature magique PDF (sécurité forte, pas d'I/O en cas d'échec)
        if not starts_with_pdf_magic(contenu):
            return SortieRecevoirEtLirePDF(
                ok=False, message="Fichier refusé : signature binaire non PDF (%PDF- absent)."
            ).model_dump()

        # 4) À partir d'ici, on est SÛR que c'est un PDF → normalisation nom + écriture
        nom = sanitize_filename(data.nom_fichier or "document.pdf")
        if not is_pdf_ext(nom):
            nom = f"{nom}.pdf"

        upload_dir = session_upload_dir(data.session_id)
        chemin_pdf = write_unique(upload_dir, nom, contenu)

        # 5) Extraction / métadonnées
        pages = count_pages(contenu)
        digest = sha256_hex(contenu)
        texte = extract_text_from_pdf_bytes(contenu)
        chunks = chunk_text(texte, max_chars=data.max_chars_per_chunk, max_chunks=data.max_chunks)
        total_chars = len(texte)

        # 6) Sauvegarde du texte brut pour la session
        text_dir = session_text_dir(data.session_id)
        os.makedirs(text_dir, exist_ok=True)
        base_txt = os.path.splitext(os.path.basename(chemin_pdf))[0] + ".txt"
        chemin_txt = os.path.join(text_dir, base_txt)
        with open(chemin_txt, "w", encoding="utf-8") as f:
            f.write(texte or "")

        # 7) Réponse OK
        return SortieRecevoirEtLirePDF(
            ok=True,
            message="PDF reçu, stocké et lu avec succès.",
            chemin_pdf=chemin_pdf,
            chemin_txt=os.path.abspath(chemin_txt),
            pages=pages,
            sha256=digest,
            chunks=chunks,
            total_chars=total_chars,
            nom_effectif=os.path.basename(chemin_pdf),
        ).model_dump()

    except Exception as e:
        # Pare-feu final : jamais d'exception non gérée côté ADK
        return SortieRecevoirEtLirePDF(ok=False, message=f"Erreur inattendue : {e}").model_dump()

def tool_spec_recevoir_et_lire_pdf() -> dict:
    """Spécification pour enregistrement dans les agents ADK."""
    return {
        "name": "recevoir_et_lire_pdf",
        "description": "Reçoit un PDF (base64), le valide, le stocke dans la session et en extrait le texte immédiatement.",
        "input_schema": EntreeRecevoirEtLirePDF.model_json_schema(),
        "output_schema": SortieRecevoirEtLirePDF.model_json_schema(),
        "handler": recevoir_et_lire_pdf,
    }