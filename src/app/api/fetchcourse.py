from fastapi import APIRouter, Form
from src.bdd import DBManager
from src.models import CourseOutput
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fetchcourse", tags=["FetchCourse"])


@router.post("", response_model=CourseOutput)
async def fetch_course(
    session_id: str = Form(...),
):
    
    """
    Récupère un cours pour une session donnée.
    Charge les données depuis la base de données.
    """
    bdd_manager = DBManager()
    
    logger.info(f"🏋️ Fetching course for session_id={session_id}")

    # Récupérer le document de la base de données
    try:
        course_object = await bdd_manager.get_document(session_id)
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du document : {e}")
        return CourseOutput(id=session_id, title="",parts=[])

    # Vérifier que le document existe
    if not course_object:
        logger.warning(f"⚠️  Aucun document trouvé pour session_id={session_id}")
        return CourseOutput(id=session_id, title="",parts=[])

    # Extraire le contenu JSON stocké
    try:
        contenu = course_object.get("contenu")
        
        # Si le contenu est une string JSON, le parser
        if isinstance(contenu, str):
            course_data = json.loads(contenu)
        else:
            course_data = contenu

        # Ajouter l'ID si absent
        if "id" not in course_data:
            course_data["id"] = session_id
        
        logger.info(f"✅ Retrieved course for session_id={session_id}")
        return CourseOutput(**course_data)
        
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
        logger.error(f"❌ Erreur lors du parsing du contenu du cours : {e}")
        return CourseOutput(id=session_id, title="",parts=[])
