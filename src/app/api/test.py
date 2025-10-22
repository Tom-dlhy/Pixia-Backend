from fastapi import APIRouter, Form, File, UploadFile
from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel
from uuid import uuid4
import logging
import json
from pathlib import Path
from google.adk.sessions import DatabaseSessionService
from src.config import database_settings, app_settings
from src.models.cours_models import CourseOutput, Part
from src.models.exercise_models import ExerciseOutput
from dotenv import load_dotenv

load_dotenv()


# Charger les données JSON des fichiers de test
def load_json_file(filename: str) -> dict:
    """Charge un fichier JSON depuis le répertoire tests/"""
    # Path(__file__).parent.parent.parent est le répertoire racine du projet
    # de src/app/api/test.py -> src/app/api -> src/app -> src -> racine
    file_path = Path(__file__).parent.parent.parent.parent / "tests" / filename
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger_instance = logging.getLogger(__name__)
        logger_instance.error(f"❌ Error loading {filename} from {file_path}: {str(e)}")
        return {}


session_service = DatabaseSessionService(db_url=database_settings.dsn)
config = app_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Test Chat"])


# -----------------------------
# ✅ Modèle de réponse
# -----------------------------
class TestChatResponse(BaseModel):
    session_id: str
    answer: str
    agent: Optional[str] = None
    redirect_id: Optional[str] = None


# -----------------------------
# ✅ Endpoint principal
# -----------------------------
@router.post("/testchat", response_model=TestChatResponse)
async def chat_endpoint(
    user_id: str = Form(...),
    message: str = Form(...),
    session_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
):
    """
    Endpoint de test pour traiter un message utilisateur.
    Accepte à la fois du texte (FormData) et des fichiers uploadés.
    """

    logger.info("🧩 Received test chat request")
    logger.info(f"user_id={user_id}, message={message}, session_id={session_id}")
    if files:
        logger.info(f"📎 {len(files)} file(s) uploaded: {[f.filename for f in files]}")

    # 🔹 Exemple : traitement simulé
    if not session_id:
        logger.info("⚡ No session_id provided, creating a new one.")
        session_id = str(uuid4())
        session_service.create_session(
            app_name=config.APP_NAME, user_id=user_id, session_id=session_id
        )
        logger.info(f"🆕 Created new session_id: {session_id}")

    if message == "genere un exercice":
        mock_agent = "exercise"
        redirect_id = f"{uuid4()}"
        mock_answer = "Voici un exercice généré pour vous."
    elif message == "genere un cours":
        mock_agent = "course"
        redirect_id = f"{uuid4()}"
        mock_answer = "Voici un cours généré pour vous."
    else:
        mock_agent = None
        redirect_id = None
        mock_answer = f"Test response to message: {message} / Agent: {mock_agent} / Redirect to: {redirect_id}"

    # 🔹 Si tu veux sauvegarder les fichiers :
    if files:
        for file in files:
            content = await file.read()
            with open(f"uploads/{file.filename}", "wb") as f:
                f.write(content)
            logger.info(f"✅ File saved: {file.filename}")

    # 🔹 Retour de la réponse typée

    logger.info(
        f"Session ID: {session_id}, Answer: {mock_answer}, Agent: {mock_agent}, Redirect ID: {redirect_id}"
    )

    return TestChatResponse(
        session_id=session_id,
        answer=mock_answer,
        agent=mock_agent,
        redirect_id=redirect_id,
    )


# -----------------------------
# ✅ Endpoint de test simple
# -----------------------------


class EventMessage(BaseModel):
    type: Literal["user", "bot", "system", "unknown"]
    text: Optional[str] = None
    timestamp: Optional[datetime] = None


class TestFetchChatResponse(BaseModel):
    session_id: Optional[str]
    user_id: str
    messages: List[EventMessage]


@router.post("/testfetchchat", response_model=TestFetchChatResponse)
async def fetch_chat(
    user_id: str = Form(...),
    session_id: Optional[str] = Form(None),
):
    user_id = "user_123"
    logger.info(
        f"📖 Fetching chat history for user_id={user_id}, session_id={session_id}"
    )  # Pour test

    session = await session_service.get_session(
        app_name=config.APP_NAME, user_id=user_id, session_id=session_id
    )

    if not session:
        logger.warning("❌ Session not found")
        return TestFetchChatResponse(
            session_id=session_id, user_id=user_id, messages=[]
        )

    messages: List[EventMessage] = []

    for e in session.events:
        # Récupération sécurisée des infos de chaque event
        evt_type = getattr(e, "event_type", "unknown")
        payload = getattr(e, "payload", {}) or {}

        # Certains events ADK contiennent le texte dans content.parts[0].text
        text = None
        if isinstance(payload, dict) and "text" in payload:
            text = payload.get("text")
        elif hasattr(e, "content") and getattr(e.content, "parts", None):
            parts = getattr(e.content, "parts", [])
            if parts and hasattr(parts[0], "text"):
                text = parts[0].text

        messages.append(
            EventMessage(
                type=evt_type, text=text, timestamp=getattr(e, "timestamp", None)
            )
        )

    logger.info(f"✅ Retrieved {len(messages)} events with text")

    return TestFetchChatResponse(
        session_id=session.id, user_id=session.user_id, messages=messages
    )


# -----------------------------
# ✅ Endpoint de test simple
# -----------------------------


class Session(BaseModel):
    session_id: str
    title: str
    course_type: str


class TestFetchAllChatResponse(BaseModel):
    sessions: List[Session]


@router.post("/testfetchallchats", response_model=TestFetchAllChatResponse)
async def fetch_all_chats(user_id: str):
    """
    Récupère l'historique de conversation pour une session donnée.
    """

    session1 = Session(
        session_id="ab840598-b044-4f97-ac8b-e112bf8c3b10",
        title="Session 1 Title",
        course_type="course",
    )
    session2 = Session(
        session_id="ab840598-b044-4f97-ac8b-e112bf8c3b11",
        title="Session 2 Title",
        course_type="exercise",
    )
    all_sessions = [session1, session2]

    return TestFetchAllChatResponse(sessions=all_sessions)


# -----------------------------
# ✅ Endpoint de test simple
# -----------------------------


class DeepCourse(BaseModel):
    deepcourse_id: str
    title: str
    completion: float


class TestFetchAllChatDeepCoursesResponse(BaseModel):
    sessions: List[DeepCourse]


@router.post(
    "/testfetchalldeepcourses", response_model=TestFetchAllChatDeepCoursesResponse
)
async def fetch_all_chats(user_id: str):
    deepcourse1 = {
        "deepcourse_id": "deepcourse-123",
        "title": "Deep Course 1 Title",
        "completion": 60.0,
    }
    deepcourse2 = {
        "deepcourse_id": "deepcourse-456",
        "title": "Deep Course 2 Title",
        "completion": 100.0,
    }

    all_deepcourses = [deepcourse1, deepcourse2]

    return TestFetchAllChatDeepCoursesResponse(sessions=all_deepcourses)


# -----------------------------
# ✅ Endpoint de test simple
# -----------------------------


class Chapter(BaseModel):
    chapter_id: str
    title: str
    is_completed: bool


class TestFetchChapterResponse(BaseModel):
    chapters: List[Chapter]


@router.post("/testfetchchapters", response_model=TestFetchChapterResponse)
async def fetch_all_chapters(user_id: str):

    chapters1 = Chapter(
        chapter_id="chapter-123",
        title="Deep Course 1 Title",
    )
    chapters2 = Chapter(
        chapter_id="chapter-456",
        title="Deep Course 2 Title",
    )

    chapters3 = Chapter(
        chapter_id="chapter-789",
        title="Deep Course 3 Title",
    )

    all_chapters = [chapters1, chapters2, chapters3]

    return TestFetchChapterResponse(chapters=all_chapters)


# -----------------------------
# ✅ Endpoint /testfetchexercise
# -----------------------------


@router.post("/testfetchexercise", response_model=ExerciseOutput)
async def fetch_exercise(
    session_id: str = Form(...),
):
    """
    Récupère un exercice pour une session donnée.
    Charge les données depuis tests/exo.json
    """
    logger.info(f"🏋️ Fetching exercise for session_id={session_id}")

    # Charger les données depuis le fichier JSON
    exo_data = load_json_file("exo.json")

    if not exo_data or "answer" not in exo_data:
        logger.error("❌ Failed to load exercise data")
        return ExerciseOutput(id=session_id, exercises=[])

    # Extraire l'exercice de la réponse
    exercise_data = exo_data.get("answer", {})

    logger.info(f"✅ Retrieved exercise")
    return ExerciseOutput(**exercise_data)


# -----------------------------
# ✅ Endpoint /testfetchcourse
# -----------------------------


@router.post("/testfetchcourse", response_model=CourseOutput)
async def fetch_course(
    session_id: str = Form(...),
):
    """
    Récupère un cours pour une session donnée.
    Charge les données depuis tests/cours.json
    """
    logger.info(f"📚 Fetching course for session_id={session_id}")

    # Charger les données depuis le fichier JSON
    course_data = load_json_file("cours.json")

    logger.info(f"📋 Raw course data: {course_data}")

    if not course_data:
        logger.error("❌ Failed to load course data - empty dict")
        raise ValueError("Could not load course data from JSON file")

    # Extraire l'answer si la structure contient answer (comme dans le JSON)
    if "answer" in course_data:
        course_data = course_data.get("answer", {})
        logger.info(f"📋 Extracted answer from course data: {course_data}")

    if not course_data or "parts" not in course_data:
        logger.error("❌ Failed to load course data - missing parts")
        raise ValueError("Could not load course data from JSON file - missing parts")

    logger.info(f"✅ Retrieved course with {len(course_data.get('parts', []))} parts")
    logger.info(f"📋 Course data before CourseOutput: {course_data}")

    return CourseOutput(**course_data)
