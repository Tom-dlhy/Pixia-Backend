from typing import Dict, Any, List
import logging

from src.config import gemini_settings
from src.models.pdf_qa_models import EntreeQuestionPDF, SortieQuestionPDF
from src.utils import get_gemini_files

logger = logging.getLogger(__name__)


def _ask_with_file(file_uri: str, question: str, max_words: int) -> Any:
    system_instruction = (
        "Tu es un assistant expert en lecture de documents PDF. "
        "Tu dois répondre uniquement à partir du contenu du PDF joint. "
        "Stratégie: (1) Recherche par mots-clés ET proches sémantiques, (2) Détection des titres/sections, (3) Extraction des passages les plus pertinents, "
        "(4) Si la question vise une phrase exacte (ex: 'par quelle phrase commence...'), renvoie la citation exacte si trouvée. "
        "(5) Si la question vise 'sous un titre', identifie le titre puis renvoie le paragraphe immédiatement en dessous. "
        f"Réponse courte (<= {max_words} mots) + JSON structuré."
    )

    user_parts = [
        {"text": question.strip()},
        {"file_data": {"file_uri": file_uri}},
    ]

    return gemini_settings.CLIENT.models.generate_content(
        model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
        contents=[{"role": "user", "parts": user_parts}],
        config={
            "system_instruction": (
                system_instruction
                + "\n\nFormat de sortie strict (JSON): {\n"
                  "  \"answer\": string,\n"
                  "  \"citations\": [ { \"page\": number|null, \"snippet\": string } ]\n"
                  "}"
            ),
            "response_mime_type": "application/json",
        },
    )


def _parse_json_response(response: Any) -> Dict[str, Any]:
    data_out = getattr(response, "parsed", None) or getattr(response, "text", None)
    if not data_out:
        return {"answer": None, "citations": []}
    if isinstance(data_out, str):
        import json
        try:
            return json.loads(data_out)
        except Exception:
            return {"answer": data_out, "citations": []}
    return data_out if isinstance(data_out, dict) else {"answer": None, "citations": []}


def repondre_question_pdf(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Répond à une question utilisateur en fouillant un PDF (mots-clés + sémantique) avec citations."""
    try:
        data = EntreeQuestionPDF(**payload)

        file_uri = data.file_uri
        if not file_uri:
            session_uris: List[str] = get_gemini_files(data.session_id)
            if len(session_uris) == 0:
                return SortieQuestionPDF(ok=False, message="Aucun PDF en contexte pour cette session.").model_dump()
            if len(session_uris) > 1:
                return SortieQuestionPDF(ok=False, message="Plusieurs PDFs en contexte - précisez 'file_uri'.").model_dump()
            file_uri = session_uris[0]

        try:
            response = _ask_with_file(file_uri, data.question, data.max_answer_words)
            parsed = _parse_json_response(response)
            answer = parsed.get("answer")
            citations = parsed.get("citations") if isinstance(parsed, dict) else []
            if answer and isinstance(citations, list):
                return SortieQuestionPDF(ok=True, message="OK", answer=answer, citations=citations).model_dump()
        except Exception:
            pass

        try:
            model_image = getattr(gemini_settings, "GEMINI_MODEL_2_5_FLASH_IMAGE", None)
            if model_image:
                response = gemini_settings.CLIENT.models.generate_content(
                    model=model_image,
                    contents=[{"role": "user", "parts": [
                        {"text": data.question.strip()},
                        {"file_data": {"file_uri": file_uri}},
                    ]}],
                    config={
                        "system_instruction": (
                            "Même consignes. Réponse courte + JSON {answer, citations}."
                        ),
                        "response_mime_type": "application/json",
                    },
                )
                parsed = _parse_json_response(response)
                answer = parsed.get("answer")
                citations = parsed.get("citations") if isinstance(parsed, dict) else []
                if answer and isinstance(citations, list):
                    return SortieQuestionPDF(ok=True, message="OK", answer=answer, citations=citations).model_dump()
        except Exception:
            pass

        return SortieQuestionPDF(ok=False, message="Impossible d'extraire une réponse fiable.").model_dump()

    except Exception as e:
        logger.exception("Erreur repondre_question_pdf")
        return SortieQuestionPDF(ok=False, message=f"Erreur: {e}").model_dump()


def tool_spec_repondre_question_pdf() -> dict:
    return {
        "name": "repondre_question_pdf",
        "description": "Repond a une question en fouillant un PDF (mots-cles + semantique) et renvoie une reponse courte avec citations (pages + extraits).",
        "input_schema": EntreeQuestionPDF.model_json_schema(),
        "output_schema": SortieQuestionPDF.model_json_schema(),
        "handler": repondre_question_pdf,
    }
