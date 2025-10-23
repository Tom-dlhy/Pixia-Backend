from fastapi import APIRouter, Form
from src.bdd import DBManager
from src.models import ExerciseOutput
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fetchchapterdocument", tags=["FetchChapterDocument"])


@router.post("", response_model=ExerciseOutput)
async def fetch_exercise(
    session_id: str = Form(...),
):
    
    """
    Récupère un exercice pour une session donnée.
    Charge les données depuis la base de données.
    """
    bdd_manager = DBManager()
    
    logger.info(f"🏋️ Fetching exercise for session_id={session_id}")

    # Récupérer le document de la base de données
    try:
        exo_data = await bdd_manager.get_document(session_id)
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du document : {e}")
        return ExerciseOutput(id=session_id, exercises=[],title="")

    # Vérifier que le document existe
    if not exo_data:
        logger.warning(f"⚠️  Aucun document trouvé pour session_id={session_id}")
        return ExerciseOutput(id=session_id, exercises=[],title="")

    # Extraire le contenu JSON stocké
    try:
        contenu = exo_data.get("contenu")
        if contenu:
        
            # Si le contenu est une string JSON, le parser
            if isinstance(contenu, str):
                exercise_data = json.loads(contenu)
            else:
                exercise_data = contenu

            # Ajouter l'ID si absent
            if "id" not in exercise_data.keys():
                exercise_data["id"] = session_id

            # Ajouter le titre si absent
            if "title" not in exercise_data.keys():
                exercise_data["title"] = ""

            logger.info(f"✅ Retrieved exercise for session_id={session_id}")
            return ExerciseOutput(**exercise_data)
        
    except (json.JSONDecodeError, ValueError, KeyError, TypeError) as e:
        logger.error(f"❌ Erreur lors du parsing du contenu de l'exercice : {e}")
        return ExerciseOutput(id=session_id, exercises=[], title="")
