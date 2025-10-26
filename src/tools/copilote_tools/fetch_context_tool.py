import logging
import json
from src.bdd import DBManager
from src.utils import get_document_id

logger = logging.getLogger(__name__)


async def fetch_context_tool() -> str:
    """
    Récupère le contenu complet du document actuel (exercise ou cours) 
    pour répondre aux questions de l'utilisateur. Utilise cet outil quand 
    tu as besoin de connaître le contenu exact du document pour aider l'utilisateur.
    
    Returns:
        Le contenu du document en format JSON string ou un message d'erreur
    """
    # Récupérer le document_id depuis le contexte
    document_id = get_document_id()
    
    if not document_id:
        logger.error("Document_id manquant dans le contexte")
        return "Erreur: ID du document non trouvé dans le contexte"
        
    try:
        db_manager = DBManager()
        
        result = await db_manager.get_document_by_id(document_id=document_id)
        
        if not result:
            logger.warning(f"Document {document_id} non trouvé")
            return f"Document {document_id} non trouvé"
        
        document_type = result.get("document_type")
        title = result.get("title")
        parsed_content = result.get("parsed_content")
        
        response = {
            "id": document_id,
            "type": document_type,
            "title": title,
            "content": parsed_content
        }
                
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du document: {e}")
        return f"Erreur lors de la récupération du document: {str(e)}"
