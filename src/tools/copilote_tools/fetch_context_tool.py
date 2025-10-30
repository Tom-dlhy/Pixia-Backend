"""Tool for retrieving document context from database.

Provides a tool for agents to fetch the complete content of an exercise or course
document to assist in responding to user questions.
"""

import json
import logging

from src.bdd import DBManager
from src.utils import get_session_id

logger = logging.getLogger(__name__)


async def fetch_context_tool() -> str:
    """
    Récupère le contenu complet du document actuel (exercise ou cours) 
    pour répondre aux questions de l'utilisateur. Utilise cet outil quand 
    tu as besoin de connaître le contenu exact du document pour aider l'utilisateur.
    
    Returns:
        Le contenu du document en format JSON string ou un message d'erreur
    """
    # Get session_id from context
    session_id = get_session_id()

    if not session_id:
        logger.error("Session ID missing from context")
        return "Error: Session ID not found in context"

    try:
        db_manager = DBManager()

        # Get dict with: id, document_type, title, parsed_content
        result = await db_manager.get_document_by_id(session_id=session_id)

        if not result:
            logger.warning(f"Document with session {session_id} not found")
            return f"Document with session {session_id} not found"

        # Extract parsed content
        document_type = result.get("document_type")
        title = result.get("title")
        parsed_content = result.get("parsed_content")

        # Build structured response
        response = {
            "id": session_id,
            "type": document_type,
            "title": title,
            "content": parsed_content,
        }

        # Return as JSON for agent parsing
        return json.dumps(response, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        return f"Error retrieving document: {str(e)}"
