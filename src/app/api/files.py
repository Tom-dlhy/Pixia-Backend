from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import os
import tempfile
from src.utils import upload_file, add_gemini_file

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
        file_id = getattr(uploaded, "name", None)
        file_state = getattr(uploaded, "state", None)
        file_uri = getattr(uploaded, "uri", None)

        # Stocker l'URI pour un usage direct par le modèle
        if file_uri:
            add_gemini_file(session_id, file_uri)

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
