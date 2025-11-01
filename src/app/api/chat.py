"""Chat endpoint for agent-based conversation with session management.

Handles user messages through the ADK runner with:
- Session persistence (in-memory or database)
- File upload and artifact management
- Retry logic for corrupted sessions
- Agent routing and tool execution
"""

import asyncio
import logging
import time
from typing import List, Optional, Union

from dotenv import load_dotenv
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.genai import types
from google.genai.types import Part

from src.agents.root_agent import root_agent
from src.config import app_settings, database_settings
from src.dto import ChatResponse
from src.models import GenerativeToolOutput
from src.utils import final_context_builder, set_request_context

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])
settings = app_settings


db_session_service = DatabaseSessionService(
    db_url=database_settings.dsn,
)

artifact_service = InMemoryArtifactService()

inmemory_service = InMemorySessionService()

current_session_service: Union[InMemorySessionService, DatabaseSessionService, None]


@router.post("", response_model=ChatResponse)
async def chat(
    user_id: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    deep_course_id: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
    message_context: Optional[str] = Form(None),
):
    """Process a user message through an ADK session."""
    start_time = time.monotonic()

    set_request_context(
        document_id=document_id,
        session_id=session_id,
        user_id=user_id,
        deep_course_id=deep_course_id,
    )

    txt_reponse: Optional[str] = None
    agent = None
    redirect_id = None
    current_session_service = None
    is_first_message = False

    try:
        # Look for existing session (in memory OR in database)
        session = None
        current_session_service = None
        
        if session_id:
            # Try in memory FIRST
            session = await inmemory_service.get_session(
                app_name=settings.APP_NAME, user_id=user_id, session_id=session_id
            )
            
            if session:
                current_session_service = inmemory_service
            
                logger.info(f"Session found in memory: {session_id}")
            else:
                # Fallback: search in database
                session = await db_session_service.get_session(
                    app_name=settings.APP_NAME, user_id=user_id, session_id=session_id
                )
                
                if session:
                    current_session_service = db_session_service
                    is_first_message = False
                    logger.info(f"Session found in database: {session_id}")
                else:
                    # Session doesn't exist anywhere
                    logger.warning(f"Session {session_id} not found (memory or database)")
                    # Create new session in DB for this session_id
                    session = await db_session_service.create_session(
                        app_name=settings.APP_NAME, 
                        user_id=user_id,
                        session_id=session_id
                    )
                    current_session_service = db_session_service
        
                    logger.info(f"New session created in database: {session_id}")

        else:
            # No session_id provided, create new one in DB
            session = await db_session_service.create_session(
                app_name=settings.APP_NAME, user_id=user_id
            )
            session_id = session.id
            current_session_service = db_session_service
    
            logger.info(f"New session created in database: {session_id}")
        
        if len(session.events) == 0:
            is_first_message = True
            
        print(f"Session ID: {session_id} | service: {type(current_session_service).__name__} | first_msg: {is_first_message}")
    except Exception as e:
        logger.exception("Error during session management")
        raise HTTPException(status_code=500, detail=f"Session error: {e}")

    if files:
        logger.info(f"Received {len(files)} file(s)")
        for idx, upload_file in enumerate(files):
            try:

                file_bytes = await upload_file.read()
                file_mime_type = upload_file.content_type or "application/octet-stream"
                filename = upload_file.filename or f"file_{idx}"

                artifact_part = types.Part.from_bytes(
                    data=file_bytes, mime_type=file_mime_type
                )

                version = await artifact_service.save_artifact(
                    app_name=settings.APP_NAME,
                    user_id=user_id,
                    session_id=session_id,
                    filename=filename,
                    artifact=artifact_part,
                )

            except Exception as e:
                logger.error(
                    f"Error saving file {filename}: {e}"
                )


    try:
        if current_session_service is None:
            return ChatResponse(
                session_id=session_id,
                answer="An error occurred during session management.",
                agent=agent,
                redirect_id=redirect_id,
            )

        if is_first_message:
            try:
                message_context = await final_context_builder(
                    message_context=message_context
                )
                message = message_context + message
            except Exception as e:
                logger.warning(f"Error enriching context: {e}")

        parts = [Part(text=message)]

        try:
            artifact_keys = await artifact_service.list_artifact_keys(
                app_name=settings.APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )

            if artifact_keys:
                logger.info(
                    f"Loading {len(artifact_keys)} artifact(s) for context"
                )
                for artifact_key in artifact_keys:
                    artifact_part = await artifact_service.load_artifact(
                        app_name=settings.APP_NAME,
                        user_id=user_id,
                        session_id=session_id,
                        filename=artifact_key,
                    )
                    if artifact_part:
                        parts.append(artifact_part)
                        logger.info(f"Artifact added to context: {artifact_key}")
        except Exception as e:
            logger.warning(f"Error loading artifacts: {e}")

        try:
            for fid in get_gemini_files(session_id):  # type: ignore[arg-type]
                parts.append(Part.from_uri(file_uri=fid, mime_type="application/pdf"))
        except Exception:
            pass

        typed_message = types.Content(role="user", parts=parts)

        # RETRY LOOP - Max 3 attempts to handle corrupted sessions
        max_retries = 3
        retry_count = 0
        execution_session_id = session_id
        last_error = None

        while retry_count < max_retries:
            try:
                retry_count += 1
                logger.info(
                    f"[ATTEMPT {retry_count}/{max_retries}] "
                    f"Running agent with session_id={execution_session_id}"
                )

                runner = Runner(
                    agent=root_agent,
                    app_name=settings.APP_NAME,
                    session_service=current_session_service,
                    artifact_service=artifact_service,
                )
            

                # Flag to track if we received at least one valid event
                received_valid_event = False
                null_event_count = 0

                async for event in runner.run_async(
                    user_id=user_id, session_id=execution_session_id, new_message=typed_message
                ):
                    # Detection of corrupted events
                    if event.content is None:
                        null_event_count += 1
                        logger.warning(
                            f"[EVENT-NULL #{null_event_count}] Event received with content=None | "
                            f"type={type(event).__name__}"
                        )
                        # If too many NULL events in a row, suspicious
                        if null_event_count > 2:
                            logger.error(
                                f"Too many NULL events ({null_event_count}), "
                                f"session probably corrupted"
                            )
                            raise RuntimeError(
                                f"Corrupted session: {null_event_count} consecutive NULL events"
                            )
                        continue

                    # At least one valid event received
                    received_valid_event = True
                    null_event_count = 0  # Reset counter
                    logger.debug(
                        f"Event received: type={type(event).__name__} | has_content={event.content is not None}"
                    )
                    print(f"Event received: {event}")

                    # Extract tool responses
                    if hasattr(event, "get_function_responses"):
                        func_responses = event.get_function_responses()
                        if func_responses:
                            for fr in func_responses:
                                tool_name = fr.name
                                tool_resp = fr.response
                                if tool_name and tool_resp:
                                    tool_result = tool_resp.get("result")
                                    logger.info(
                                        f"Tool executed: {tool_name} | "
                                        f"result_type={type(tool_result).__name__}"
                                    )

                                    if tool_name in (
                                        "generate_exercises",
                                        "generate_courses",
                                        "generate_new_chapter",
                                        "generate_deepcourse",
                                    ):
                                        if isinstance(tool_result, GenerativeToolOutput):
                                            agent = tool_result.agent
                                            redirect_id = tool_result.redirect_id
                                            logger.info(
                                                f"Generator completed: agent={agent}, "
                                                f"redirect_id={redirect_id}"
                                            )

                    # Detection of final response
                    if event.is_final_response():
                        logger.info("Final event detected")
                        if event.content and event.content.parts:
                            # Récupère tous les parts avec du texte et les concatène
                            text_parts = []
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                            
                            if text_parts:
                                txt_reponse = ''.join(text_parts)
                                agent = event.author
                            else:
                                logger.warning("Final event but no text content in any part")
                        else:
                            logger.warning("Final event but no text content")
                        break

                # Execution successful, exit retry loop
                if received_valid_event:
                    logger.info(f"[ATTEMPT {retry_count}] Success - At least one valid event received")
                    break
                else:
                    raise RuntimeError("No valid event received from runner")

            except (asyncio.TimeoutError, RuntimeError) as e:
                last_error = e
                logger.error(
                    f"[ATTEMPT {retry_count}/{max_retries}] Error detected: {type(e).__name__}: {e}"
                )

                # If not last attempt, delete old corrupted session and retry
                if retry_count < max_retries:
                    logger.info(f"Deleting corrupted session and retrying...")
                    try:
                        # Get current (potentially corrupted) session from SAME service
                        old_session = await current_session_service.get_session(
                            app_name=settings.APP_NAME,
                            user_id=user_id,
                            session_id=execution_session_id
                        )
                        
                        # Extract valid events
                        valid_events = []
                        if old_session:
                            if hasattr(old_session, 'events') and old_session.events:
                                # Filter events: keep only those with content
                                valid_events = [e for e in old_session.events if e.content is not None]
                                logger.info(
                                    f"{len(valid_events)}/{len(old_session.events)} valid events recovered "
                                    f"(filtered {len(old_session.events) - len(valid_events)} NULL events)"
                                )
                            else:
                                logger.warning(f"No 'events' attribute or empty")
                        else:
                            logger.error(f"Old session not found")

                        # CRITICAL: Steps to duplicate events
                        # 1. Get valid events (already done above)
                        # 2. Delete old session (CASCADE deletes its events)
                        # 3. Create new session
                        # 4. Re-insert valid events -> no conflict since old IDs are freed
                        
                        await current_session_service.delete_session(
                            app_name=settings.APP_NAME,
                            user_id=user_id,
                            session_id=execution_session_id
                        )
                        logger.info(f"Corrupted session deleted: {execution_session_id}")
                        logger.info(f"   -> {len(valid_events)} events also deleted (CASCADE)")

                        # Create NEW clean session
                        new_session = await current_session_service.create_session(
                            app_name=settings.APP_NAME, user_id=user_id
                        )
                        new_session_id = new_session.id
                        logger.info(f"New session created: {new_session_id}")
                        
                        # RE-INSERT valid events into new session
                        # Now that old session is deleted, event IDs are freed
                        if valid_events:
                            for event in valid_events:
                                await current_session_service.append_event(
                                    session=new_session,
                                    event=event
                                )
                            logger.info(f"{len(valid_events)} events duplicated to new session")
                        else:
                            logger.warning(f"No valid event to duplicate")
                        
                        # Use new session for retry
                        execution_session_id = new_session_id
                        logger.info(f"Switched to new session with restored events: {execution_session_id}")

                        # Wait before retry (exponential backoff)
                        wait_time = 2 ** (retry_count - 1)
                        logger.info(f"Waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        
                    except Exception as session_err:
                        logger.error(f"Error during session cleanup/creation: {session_err}")
                        logger.debug(f"   Traceback: ", exc_info=True)
                        raise
                else:
                    logger.error(f"Failed after {max_retries} attempts")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Persistent agent error after {max_retries} attempts: {str(last_error)}",
                    )

    except Exception as e:
        logger.exception("Error during ADK runner execution")
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    if not txt_reponse and (agent is not None and redirect_id is not None):
        txt_reponse = "Your document was generated successfully."
    elif not txt_reponse:
        txt_reponse = " "

    end_time = time.monotonic()
    duration = end_time - start_time
    print(f"Total duration: {duration:.2f} seconds")

    logger.info(f"agent={agent}")
    logger.info(f"redirect_id={redirect_id}")
    output = ChatResponse(
        session_id=session_id,
        answer=txt_reponse,
        agent=agent,
        redirect_id=redirect_id,
    )

    return output
