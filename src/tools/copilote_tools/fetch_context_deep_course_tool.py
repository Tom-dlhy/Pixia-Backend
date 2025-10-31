"""Tool for retrieving deepcourse document context from database.

Provides a tool for agents to fetch the complete content of a deepcourse
and its chapters to assist in responding to user questions.
"""

import json
import logging
from typing import Any, Dict, List

from src.bdd import DBManager
from src.utils import get_deep_course_id

logger = logging.getLogger(__name__)


async def fetch_context_deep_course_tool() -> str:
    """
    Récupère le contenu complet du document actuel (exercise ou cours) 
    pour répondre aux questions de l'utilisateur. Utilise cet outil quand 
    tu as besoin de connaître le contenu exact du document pour aider l'utilisateur.
    
    Returns:
        Le contenu du document en format JSON string ou un message d'erreur
    """
    # Get deepcourse_id from context
    deepcourse_id = get_deep_course_id()

    if not deepcourse_id:
        logger.error("DeepCourse ID missing from context")
        return "Error: DeepCourse ID not found in context"

    try:
        db_manager = DBManager()
        deepcourse_data_list: List[Dict[str, Any]] = (
            await db_manager.get_deepcourse_and_chapter_with_id(deepcourse_id)
        )

        if not deepcourse_data_list:
            logger.warning(f"No data found for deepcourse_id={deepcourse_id}")
            return f"No deepcourse found with ID: {deepcourse_id}"

        return json.dumps(deepcourse_data_list, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception(f"Error retrieving deepcourse: {e}")
        return f"Error retrieving deepcourse: {str(e)}"
    
        
     


