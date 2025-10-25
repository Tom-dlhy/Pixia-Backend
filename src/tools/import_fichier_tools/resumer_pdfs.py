from typing import Dict, Any, List
from src.config import gemini_settings
from src.models.pdf_summary_models import EntreeResumerPDFs, SortieResumerPDFs
from src.utils import get_gemini_files

def resumer_pdfs_session(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Génère un résumé concis des PDF présents dans le contexte de session (Gemini files)."""
    try:
        data = EntreeResumerPDFs(**payload)
        file_ids: List[str] = data.file_ids or get_gemini_files(data.session_id)

        uris: List[str] = []
        for fid in file_ids:
            if isinstance(fid, str) and fid.startswith("files/"):
                try:
                    f = gemini_settings.CLIENT.files.get(name=fid)
                    uri = getattr(f, "uri", None)
                    if uri:
                        uris.append(uri)
                except Exception:
                    continue
            else:
                uris.append(fid)
        file_ids = uris

        if not file_ids:
            return SortieResumerPDFs(
                ok=False,
                message="Aucun PDF en contexte pour cette session.",
                summary=None,
            ).model_dump()

        instruction = (
            "Tu es un assistant qui résume des documents PDF. "
            "Procède par: (1) survol global, (2) détection des titres/sections, (3) extraction des passages clés, "
            "(4) synthèse structurée en quelques points, en français, sans préambule. "
            "Si le PDF est scanné, appuie-toi sur la compréhension d'image du modèle."
        )
        user_parts = [{"file_data": {"file_uri": uri}} for uri in file_ids[:5]]

        try:
            response = gemini_settings.CLIENT.models.generate_content(
                model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
                contents=[{"role": "user", "parts": user_parts}],
                config={
                    "system_instruction": instruction,
                    "response_mime_type": "text/plain",
                },
            )
            summary = getattr(response, "text", None) or getattr(response, "parsed", None)
            if isinstance(summary, str) and summary.strip():
                return SortieResumerPDFs(ok=True, message="Résumé généré avec succès.", summary=summary).model_dump()
        except Exception:
            pass

        model_image = getattr(gemini_settings, "GEMINI_MODEL_2_5_FLASH_IMAGE", None)
        if model_image:
            response = gemini_settings.CLIENT.models.generate_content(
                model=model_image,
                contents=[{"role": "user", "parts": user_parts}],
                config={
                    "system_instruction": instruction,
                    "response_mime_type": "text/plain",
                },
            )
            summary = getattr(response, "text", None) or getattr(response, "parsed", None)
            if isinstance(summary, str) and summary.strip():
                return SortieResumerPDFs(ok=True, message="Résumé généré avec succès.", summary=summary).model_dump()

        return SortieResumerPDFs(ok=False, message="Impossible de générer un résumé fiable.", summary=None).model_dump()

    except Exception as e:
        return SortieResumerPDFs(
            ok=False,
            message=f"Erreur lors du résumé: {e}",
            summary=None,
        ).model_dump()


def tool_spec_resumer_pdfs_session() -> dict:
    return {
        "name": "resumer_pdfs_session",
        "description": "Résume les PDF présents dans le contexte de la session (Gemini).",
        "input_schema": EntreeResumerPDFs.model_json_schema(),
        "output_schema": SortieResumerPDFs.model_json_schema(),
        "handler": resumer_pdfs_session,
    }
