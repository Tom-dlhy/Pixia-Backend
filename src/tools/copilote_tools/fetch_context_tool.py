import logging
import json
from contextvars import ContextVar
from src.bdd import DBManager

logger = logging.getLogger(__name__)

_document_id_context: ContextVar[str] = ContextVar('document_id', default='')


def set_document_id_context(document_id: str):
    """Définit le document_id dans le contexte de la requête."""
    _document_id_context.set(document_id)


async def fetch_context_tool() -> str:
    """
    Récupère le contenu complet du document actuel (exercise ou cours) 
    pour répondre aux questions de l'utilisateur. Utilise cet outil quand 
    tu as besoin de connaître le contenu exact du document pour aider l'utilisateur.
    
    Returns:
        Le contenu du document en format JSON string ou un message d'erreur
    """
    document_id = _document_id_context.get()
    
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
