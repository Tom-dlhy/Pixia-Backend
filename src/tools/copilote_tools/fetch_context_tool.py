"""Tool pour récupérer le contexte d'un document (exercise ou cours)."""
import logging
import json
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
    # Récupérer le session_id depuis le contexte
    session_id = get_session_id()
    
    if not session_id:
        logger.error("❌ session_id manquant dans le contexte")
        return "Erreur: ID de session non trouvé dans le contexte"
    
    try:
        db_manager = DBManager()
        
        # Récupère un dict avec: id, document_type, title, parsed_content
        result = await db_manager.get_document_by_id(session_id=session_id)
        
        if not result:
            logger.warning(f"⚠️ Document avec session : {session_id} non trouvé")
            return f"Document avec session : {session_id} non trouvé"

        # Extraire le contenu parsé
        document_type = result.get("document_type")
        title = result.get("title")
        parsed_content = result.get("parsed_content")
        
        # Construire la réponse structurée
        response = {
            "id": session_id,
            "type": document_type,
            "title": title,
            "content": parsed_content
        }

        # Retourner en JSON pour que l'agent puisse le parser
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération du document: {e}")
        return f"Erreur lors de la récupération du document: {str(e)}"
