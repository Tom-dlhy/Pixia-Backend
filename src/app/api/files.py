from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import tempfile
from src.utils import upload_file, add_gemini_file, add_gemini_file_name

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload")
async def upload_pdf(session_id: str = Form("default"), file: UploadFile = File(...)):
    # Basic validation: only PDFs
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF")

    # Save to a temporary file to forward to Gemini
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        uploaded = upload_file(tmp_path)
        file_id = getattr(uploaded, "name", None)  # resource name for deletion
        file_state = getattr(uploaded, "state", None)
        file_uri = getattr(uploaded, "uri", None)  # URI for model usage

        # Stocker l'URI pour un usage direct par le modèle
        if file_uri:
            add_gemini_file(session_id, file_uri)
        if file_id:
            add_gemini_file_name(session_id, file_id)

        return {
            "ok": True,
            "message": "Fichier uploadé vers Gemini et ajouté au contexte de session.",
            "filename": file.filename,
            "gemini_file_id": file_id,
            "gemini_state": file_state,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload Gemini: {e}")
    finally:
        try:
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


@router.post("/purge")
async def purge_session_files(session_id: str = Form("default")):
    """Supprime les fichiers Gemini liés à une session et nettoie le contexte en mémoire."""
    from src.utils import get_gemini_files, get_gemini_file_names, clear_session, delete_file
    from src.config import gemini_settings

    deleted = 0
    errors: list[str] = []

    # 1) Supprimer via les noms (resource name) si disponibles
    names = get_gemini_file_names(session_id)
    for name in names:
        try:
            delete_file(name)
            deleted += 1
        except Exception as e:
            errors.append(f"{name}: {e}")

    # 2) Pour les URIs restantes sans nom, tenter de résoudre via list() puis supprimer
    uris = set(get_gemini_files(session_id))
    try:
        # list() paginé potentiel — pour simplicité, on itère une fois
        listing = gemini_settings.CLIENT.aio.files.list()
        for f in getattr(listing, "files", []) or []:
            uri = getattr(f, "uri", None)
            name = getattr(f, "name", None)
            if uri in uris and name:
                try:
                    delete_file(name)
                    deleted += 1
                    uris.remove(uri)
                except Exception as e:
                    errors.append(f"{name}: {e}")
    except Exception as e:
        errors.append(f"list(): {e}")

    # 3) Nettoyage contexte mémoire
    clear_session(session_id)

    return {
        "ok": True,
        "deleted": deleted,
        "remaining_uris": list(uris),
        "errors": errors,
    }
