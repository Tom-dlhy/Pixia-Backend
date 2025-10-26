import time
import logging
from typing import Any

from src.config import gemini_settings

logger = logging.getLogger(__name__)


def upload_file(file_path: str) -> Any:
    """Upload file to Gemini et retourne l'objet fichier (Client File)."""
    try:
        uploaded_file = gemini_settings.CLIENT.files.upload(file=file_path)  

        while getattr(uploaded_file, "state", None) == "PROCESSING":
            time.sleep(0.5)
            uploaded_file = gemini_settings.CLIENT.files.get(name=uploaded_file.name)  

        if getattr(uploaded_file, "state", None) == "FAILED":
            raise Exception("Échec du traitement du fichier")

        return uploaded_file

    except Exception as e:
        raise Exception(f"Error uploading file to Gemini: {str(e)}")


def delete_file(file_id: str) -> None:
    """Supprime un fichier côté Gemini par son ID (resource name)."""
    try:
        gemini_settings.CLIENT.files.delete(name=file_id) 
    except Exception as e:
        raise Exception(f"Error deleting file {file_id}: {str(e)}")

