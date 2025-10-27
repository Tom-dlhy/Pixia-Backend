from fastapi import APIRouter, Form, HTTPException
from src.bdd import DBManager
from src.models import ExerciseOutput, CourseOutput
import logging
import json
from pydantic import BaseModel

from src.utils.save_files import generate_course_pdf_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloadcourse", tags=["DownloadCourse"])


@router.post("")
async def download_course(
    session_id: str = Form(...),
):
    """
    Télécharge le PDF d'un cours à partir de son session_id.

    Args:
        session_id: ID de session du cours à télécharger

    Returns:
        Response: PDF du cours avec nom de fichier automatique
    """
    try:
        dbmanager = DBManager()
        test_course = await dbmanager.get_document_by_session_id(session_id)

        if not test_course:
            logger.warning(f"❌ Aucun cours trouvé pour session_id: {session_id}")
            raise HTTPException(
                status_code=404, detail="Cours non trouvé pour ce session_id"
            )

        contenu = test_course.get("contenu")

        # Si le contenu est une string JSON, le parser
        if isinstance(contenu, str):
            course_data = json.loads(contenu)
        else:
            course_data = contenu

        objet_course = CourseOutput.model_validate(course_data)

        return generate_course_pdf_response(objet_course)

    except json.JSONDecodeError as e:
        logger.error(f"❌ Erreur de parsing JSON: {e}")
        raise HTTPException(
            status_code=500, detail="Erreur lors du parsing du contenu du cours"
        )
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération du PDF: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du PDF: {str(e)}"
        )
