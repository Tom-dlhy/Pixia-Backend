from fastapi import APIRouter, Depends, HTTPException, UploadFile
from src.dto import ChatResponse, ChatRequest, build_chat_response
from src.config import database_settings, app_settings
from src.agents.root_agent import root_agent
from src.models import _validate_exercise_output, _validate_course_output
from src.utils import generate_title_from_messages
from src.bdd import DBManager
from src.models import ExerciseOutput, CourseOutput

from typing import List, Optional, Union
from uuid import uuid4
from google.adk.sessions import Session, InMemorySessionService
from google.adk.runners import Runner
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types
from google.genai.types import Part
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = app_settings


session_service = DatabaseSessionService(
    db_url=database_settings.dsn, 
)

inmemory_service = InMemorySessionService()

@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Traite un message utilisateur via une session ADK."""

    user_id: str = req.user_id
    message: str = req.message
    session_id: Optional[str] = req.session_id  # None si nouvelle conversation
    files = req.files or []  # support fichiers futur
    title: Optional[str]  = None  # support titre futur

    final_response: Optional[Union[str, dict, list]] = None
    author: Optional[str] = None
    bdd_manager = DBManager()

    # === Étape 1 : création ou récupération de session ===
    try:
        if session_id :
            session = await inmemory_service.get_session(
                app_name=settings.APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            if session : 
                session_id = session.id
            else : 
                session = await session_service.get_session(
                app_name=settings.APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
         
        elif not session_id:
            logger.info(f"🆕 Création d'une nouvelle session pour l'utilisateur {user_id}")
            session = await inmemory_service.create_session(
                app_name=settings.APP_NAME,
                user_id=user_id
            )
            session_id = session.id
            # title = await generate_title_from_messages(message)
            # # TODO : gérer le cas où c'est un deep course et passer is_deepcourse=True
            # if isinstance(title, str):
            #     await bdd_manager.create_session_title(session_id, title)
            # else:
            #     logger.warning("⚠️ Le titre généré n'est pas une chaîne de caractères valide.")  

        # else:
        #     logger.info(f"🔄 Chargement de la session existante {session_id} pour {user_id}")
        #     session = await session_service.get_session(
        #         app_name=settings.APP_NAME,
        #         user_id=user_id,
        #         session_id=session_id
        #     )  
        # logger.info(f"✅ Session opérationnelle : {session_id}")

    except Exception as e:
        logger.exception("❌ Erreur pendant la gestion de la session")
        raise HTTPException(status_code=500, detail=f"Erreur de session : {e}")

    # === Étape 2 : exécution du runner ADK ===
    try:
        typed_message = types.Content(role="user", parts=[Part(text=message)])
        runner = Runner(
            agent=root_agent,
            app_name=settings.APP_NAME,
            session_service=session_service
        )

        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=typed_message
        ):

            # --- Réponse finale ---
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text

                    logger.info(f"✅ Réponse finale reçue pour la session {session_id}")
                    author = event.author
                break

            # --- Sortie d’un outil (tool output) ---
            elif hasattr(event, "get_function_responses"):
                func_responses = event.get_function_responses()
                if func_responses:
                    for fr in func_responses:
                        tool_name = fr.name
                        tool_resp = fr.response

                        if tool_name == "generate_exercises":
                            logger.info("✅ Tool 'generate_exercises' détecté")
                            if _validate_exercise_output(tool_resp):
                                copilote_session_id = str(uuid4())
                                await session_service.create_session(
                                    session_id=copilote_session_id,
                                    app_name=settings.APP_NAME,
                                    user_id=user_id
                                )
                                final_response = _validate_exercise_output(tool_resp)
                                if isinstance(final_response, ExerciseOutput):
                                    logger.info(f"✅ ExerciseOutput validé pour la session {session_id}")
                                    await bdd_manager.store_basic_document(content=final_response, session_id=copilote_session_id, sub=user_id)
                                author = event.author
                            
                        elif tool_name == "generate_courses":
                            logger.info("✅ Tool 'generate_courses' détecté")
                            if _validate_course_output(tool_resp):
                                copilote_session_id = str(uuid4())
                                await session_service.create_session(
                                    session_id=copilote_session_id,
                                    app_name=settings.APP_NAME,
                                    user_id=user_id
                                )
                                final_response = _validate_course_output(tool_resp)
                                if isinstance(final_response, CourseOutput):
                                    logger.info(f"✅ CourseOutput validé pour la session {session_id}")
                                    await bdd_manager.store_basic_document(content=final_response, session_id=copilote_session_id, sub=user_id)
                                author = event.author

                        elif tool_name == "modify_course":
                            logger.info("✅ Tool 'modify_course' détecté")
                            if _validate_course_output(tool_resp):
                                final_response = _validate_course_output(tool_resp)
                                if isinstance(final_response, CourseOutput):
                                    logger.info(f"✅ CourseOutput validé pour la session {session_id}")
                                    await bdd_manager.update_document(document_id=session_id, new_content=final_response)
                                author = event.author

                        elif tool_name == "delete_course":
                            logger.info("✅ Tool 'delete_course' détecté")
                            await bdd_manager.delete_document(document_id=session_id)

                        elif tool_name == "generate_deepcourse":
                            deepcourse_id = str(uuid4())
                            if isinstance(final_response, DeepCourseOutput):    
                                logger.info(f"✅ DeepCourseOutput validé pour la session {session_id}")
                                await bdd_manager.store_deepcourse(deepcourse_id=deepcourse_id, content=final_response)
                        
                        elif tool_name == "generate_new_chapter_deepcourse":
                            logger.info("✅ Tool 'generate_new_chapter_deepcourse' détecté")
                            await 
                            

    except Exception as e:
        logger.exception("❌ Erreur pendant l'exécution du runner ADK")
        raise HTTPException(status_code=500, detail=f"Erreur agent : {e}")

    # === Étape 3 : validation finale ===
    if not final_response:
        logger.error(f"Aucune réponse reçue pour la session {session_id}")
        raise HTTPException(status_code=500, detail="Aucune réponse de l’agent.")

    # === Étape 4 : construction de la réponse ===
    return build_chat_response(
        chat_id=session_id,  # TODO : renommer chat_id → session_id dans le DTO
        agent_used=author or "unknown",  # Fallback si l’auteur n’est pas défini
        raw_answer=final_response
    )