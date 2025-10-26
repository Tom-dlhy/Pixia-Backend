"""Tool pour récupérer le contexte d'un document (exercise ou cours)."""
import logging
import json
from src.bdd import DBManager
from src.utils import get_deep_course_id
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


async def fetch_context_deep_course_tool() -> str:
    """
    Récupère le contenu complet du document actuel (exercise ou cours) 
    pour répondre aux questions de l'utilisateur. Utilise cet outil quand 
    tu as besoin de connaître le contenu exact du document pour aider l'utilisateur.
    
    Returns:
        Le contenu du document en format JSON string ou un message d'erreur
    """
    # Récupérer le deepcourse_id depuis le contexte
    deepcourse_id = get_deep_course_id()
    
    if not deepcourse_id:
        logger.error("❌ deepcourse_id manquant dans le contexte")
        return "Erreur: ID du deepcourse non trouvé dans le contexte"
    
    try:
        db_manager = DBManager()
        deepcourse_data_list: List[Dict[str, Any]] = (
            await db_manager.get_deepcourse_and_chapter_with_id(deepcourse_id)
        )
        
        if not deepcourse_data_list:
            logger.warning(f"⚠️ Aucune donnée trouvée pour deepcourse_id={deepcourse_id}")
            return f"Aucun deepcourse trouvé avec l'ID: {deepcourse_id}"
        
        return json.dumps(deepcourse_data_list, ensure_ascii=False, indent=2)
    
    except Exception as e:
        logger.exception(f"❌ Erreur lors de la récupération du deepcourse: {e}")
        return f"Erreur lors de la récupération du deepcourse: {str(e)}"
    
        
     


