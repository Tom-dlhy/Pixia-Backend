"""Asynchronous database manager for backend operations.

Handles all database operations using SQLAlchemy async engine with PostgreSQL.
Manages initialization, CRUD operations for documents, chapters, and deep courses.

Some functions are created but not yet used in the codebase.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import uuid4

import json
from google.adk.sessions import DatabaseSessionService
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.bdd.query import (
    CHANGE_SETTINGS,
    CHECK_TABLES,
    CLEAR_ALL_TABLES,
    CORRECT_PLAIN_QUESTION,
    CREATE_CHAPTER,
    CREATE_DEEPCOURSE,
    DELETE_CHAPTER,
    DELETE_DEEPCOURSE,
    DELETE_DOCUMENTS,
    DELETE_DOCUMENTS_BY_CHAPTER,
    DROP_ALL_TABLES,
    FETCH_ALL_CHAPTERS,
    FETCH_ALL_CHATS,
    FETCH_ALL_DEEPCOURSES,
    FETCH_CHAPTER_DOCUMENTS,
    FETCH_DOCUMENT_BY_SESSION,
    FETCH_DOCUMENT_CONTENT_BY_ID,
    GET_DEEPCOURSE_AND_CHAPTER_FROM_ID,
    GET_SESSION_FROM_DOCUMENT,
    LOGIN_USER,
    MARK_CHAPTER_COMPLETE,
    MARK_CHAPTER_UNCOMPLETE,
    MARK_IS_CORRECTED_QCM,
    RENAME_CHAPTER,
    SIGNUP_USER,
    STORE_BASIC_DOCUMENT,
    UPDATE_DOCUMENT_CONTENT,
)
from src.bdd.schema_sql import Base
from src.config import database_settings
from src.models import CourseOutput, DeepCourseOutput, ExerciseOutput


# Database URL configuration
DATABASE_URL_SYNC = database_settings.dsn

# Convert sync DSN to async DSN
if "+asyncpg" not in DATABASE_URL_SYNC:
    if "+psycopg2" in DATABASE_URL_SYNC:
        DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace("+psycopg2", "+asyncpg")
    else:
        DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
else:
    DATABASE_URL_ASYNC = DATABASE_URL_SYNC

print("🧩 Async DSN:", DATABASE_URL_ASYNC)


class DBManager:
    """
    Asynchronous database manager.

    Handles all database operations with async/await pattern.
    Uses ADK's sync engine for initial schema creation, then manages
    all backend operations through an async SQLAlchemy engine.
    """

    def __init__(self):
        """Initialize async engine and session factory."""
        # Async engine for all backend operations
        self.engine = create_async_engine(DATABASE_URL_ASYNC, echo=False, future=True)
        self.SessionLocal = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        print("⚙️  Async engine initialized (backend).")

    # -----------------------------------------------------
    # CRÉATION COMPLÈTE DE LA BASE VIA ADK
    # -----------------------------------------------------
    async def create_db(self):
        """
        Initialize complete database.

        - Uses ADK (sync) to create its core tables (sessions, events, states)
        - Creates business logic tables on the same engine
        - Recreates async engine for backend
        """
        print("🚀 Complete database initialization via ADK...")

        # 1. Launch ADK (sync) → creates its own tables
        adk_service = DatabaseSessionService(db_url=DATABASE_URL_SYNC)
        adk_engine = adk_service.db_engine

        # 2. Create business logic tables on ADK engine
        Base.metadata.create_all(bind=adk_engine)
        print("✅ ADK + business logic tables created (via ADK sync engine).")

        # 3. Recreate async engine for backend
        self.engine = create_async_engine(DATABASE_URL_ASYNC, echo=False, future=True)
        self.SessionLocal = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        print("🔄 Async engine restored for backend.")

    async def get_db(self):
        """Context manager for async database session."""
        async with self.SessionLocal() as session:
            yield session

    async def clear_tables(self):
        """Clear all tables without dropping them."""
        async with self.engine.begin() as conn:
            await conn.execute(CLEAR_ALL_TABLES)
        print("🧹 Tables cleared.")

    async def clear_db(self):
        """Drop all tables (ADK + business logic)."""
        async with self.engine.begin() as conn:
            await conn.execute(DROP_ALL_TABLES)
        print("💣 All tables dropped.")

    async def test_db(self):
        """Test database connection and list existing tables."""
        async with self.engine.begin() as conn:
            result = await conn.execute(CHECK_TABLES)
            tables = [row[0] for row in result.fetchall()]
        print("📋 Existing tables:", tables)
        return tables

    # Chat operations
    async def fetch_all_chats(self, user_id: str):
        """Fetch all chat sessions for a given user."""
        async with self.engine.begin() as conn:
            result = await conn.execute(FETCH_ALL_CHATS, {"user_id": user_id})
            sessions = [dict(row._mapping) for row in result.fetchall()]
        return sessions

    # Document operations
    async def store_basic_document(
        self,
        content: Union[ExerciseOutput, CourseOutput],
        session_id: str,
        sub: str,
        chapter_id: Optional[str] = None,
    ):
        """Store a document (exercise or course) associated with a session."""
        doc_type = (
            "exercise"
            if isinstance(content, ExerciseOutput)
            else "course" if isinstance(content, CourseOutput) else "eval"
        )
        document_id = content.id
        created_at = datetime.now()
        updated_at = created_at
        chapter_id = chapter_id if chapter_id else None
        contenu_json = json.dumps(
            content.model_dump() if hasattr(content, "model_dump") else content
        )

        async with self.engine.begin() as conn:
            await conn.execute(
                STORE_BASIC_DOCUMENT,
                {
                    "id": document_id,
                    "google_sub": sub,
                    "session_id": session_id,
                    "chapter_id": chapter_id,
                    "document_type": doc_type,
                    "contenu": contenu_json,
                    "created_at": created_at,
                    "updated_at": updated_at,
                },
            )

    async def delete_document(self, document_id: str):
        """Delete a document."""
        async with self.engine.begin() as conn:
            await conn.execute(DELETE_DOCUMENTS, {"document_id": document_id})

    async def update_document(
        self, document_id: str, new_content: Union[ExerciseOutput, CourseOutput]
    ):
        """Update document content."""
        contenu_json = json.dumps(
            new_content.model_dump()
            if hasattr(new_content, "model_dump")
            else new_content
        )
        async with self.engine.begin() as conn:
            await conn.execute(
                UPDATE_DOCUMENT_CONTENT, {"id": document_id, "contenu": contenu_json}
            )

    async def fetch_all_deepcourses(self, user_id: str):
        """Fetch all deep courses for a given user."""
        async with self.engine.begin() as conn:
            result = await conn.execute(FETCH_ALL_DEEPCOURSES, {"user_id": user_id})
            deepcourses = [dict(row._mapping) for row in result.fetchall()]
        return deepcourses

    async def get_deepcourse_and_chapter_with_id(self, deepcourse_id):
        """Fetch deep course and its chapters by deep course ID."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                GET_DEEPCOURSE_AND_CHAPTER_FROM_ID, {"deepcourse_id": deepcourse_id}
            )
            chapters = [dict(row._mapping) for row in result.fetchall()]
        return chapters

    async def store_chapter(
        self,
        title,
        user_id,
        deepcourse_id,
        chapter_id,
        session_exercise,
        session_course,
        session_evaluation,
        exercice,
        course,
        evaluation,
    ):
        """Store a chapter of a deep course with its exercise, course, and evaluation."""
        now = datetime.now()

        async with self.engine.begin() as conn:
            await conn.execute(
                CREATE_CHAPTER,
                {
                    "id": chapter_id,
                    "deep_course_id": deepcourse_id,
                    "titre": title,
                    "is_complete": False,
                },
            )
            exercise_json = json.dumps(
                exercice.model_dump() if hasattr(exercice, "model_dump") else exercice
            )
            await conn.execute(
                STORE_BASIC_DOCUMENT,
                {
                    "id": exercice.id,
                    "google_sub": user_id,
                    "session_id": session_exercise,
                    "chapter_id": chapter_id,
                    "document_type": "exercise",
                    "contenu": exercise_json,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            course_json = json.dumps(
                course.model_dump() if hasattr(course, "model_dump") else course
            )
            await conn.execute(
                STORE_BASIC_DOCUMENT,
                {
                    "id": course.id,
                    "google_sub": user_id,
                    "session_id": session_course,
                    "chapter_id": chapter_id,
                    "document_type": "course",
                    "contenu": course_json,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            evaluation_json = json.dumps(
                evaluation.model_dump()
                if hasattr(evaluation, "model_dump")
                else evaluation
            )
            await conn.execute(
                STORE_BASIC_DOCUMENT,
                {
                    "id": evaluation.id,
                    "google_sub": user_id,
                    "session_id": session_evaluation,
                    "chapter_id": chapter_id,
                    "document_type": "eval",
                    "contenu": evaluation_json,
                    "created_at": now,
                    "updated_at": now,
                },
            )

    async def store_deepcourse(
        self,
        user_id: str,
        content: DeepCourseOutput,
        dict_session: List[Dict[str, str]],
    ):
        """
        Store complete deep course.

        Creates the deep course and stores each chapter with its 3 documents
        (exercise, course, evaluation).

        Args:
            user_id: User ID (google_sub).
            content: DeepCourseOutput object with all chapters.
            dict_session: List of dicts with structure:
                [{
                    "id_chapter": str,
                    "session_id_exercise": str,
                    "session_id_course": str,
                    "session_id_evaluation": str
                }, ...]
        """
        deepcourse_id = content.id or str(uuid4())

        async with self.engine.begin() as conn:
            await conn.execute(
                CREATE_DEEPCOURSE,
                {"id": deepcourse_id, "titre": content.title, "google_sub": user_id},
            )

            for idx, chapter in enumerate(content.chapters):
                chapter_id = chapter.id_chapter or str(uuid4())

                await conn.execute(
                    CREATE_CHAPTER,
                    {
                        "id": chapter_id,
                        "deep_course_id": deepcourse_id,
                        "titre": chapter.title,
                        "is_complete": False,
                    },
                )

                chapter_sessions = dict_session[idx]
                session_exercise = chapter_sessions["session_id_exercise"]
                session_course = chapter_sessions["session_id_course"]
                session_evaluation = chapter_sessions["session_id_evaluation"]

                now = datetime.now()

                exercise_id = chapter.exercice.id or str(uuid4())
                exercise_json = json.dumps(
                    chapter.exercice.model_dump()
                    if hasattr(chapter.exercice, "model_dump")
                    else chapter.exercice
                )
                await conn.execute(
                    STORE_BASIC_DOCUMENT,
                    {
                        "id": exercise_id,
                        "google_sub": user_id,
                        "session_id": session_exercise,
                        "chapter_id": chapter_id,
                        "document_type": "exercise",
                        "contenu": exercise_json,
                        "created_at": now,
                        "updated_at": now,
                    },
                )

                course_id = chapter.course.id or str(uuid4())
                course_json = json.dumps(
                    chapter.course.model_dump()
                    if hasattr(chapter.course, "model_dump")
                    else chapter.course
                )
                await conn.execute(
                    STORE_BASIC_DOCUMENT,
                    {
                        "id": course_id,
                        "google_sub": user_id,
                        "session_id": session_course,
                        "chapter_id": chapter_id,
                        "document_type": "course",
                        "contenu": course_json,
                        "created_at": now,
                        "updated_at": now,
                    },
                )

                evaluation_id = chapter.evaluation.id or str(uuid4())
                evaluation_json = json.dumps(
                    chapter.evaluation.model_dump()
                    if hasattr(chapter.evaluation, "model_dump")
                    else chapter.evaluation
                )
                await conn.execute(
                    STORE_BASIC_DOCUMENT,
                    {
                        "id": evaluation_id,
                        "google_sub": user_id,
                        "session_id": session_evaluation,
                        "chapter_id": chapter_id,
                        "document_type": "eval",
                        "contenu": evaluation_json,
                        "created_at": now,
                        "updated_at": now,
                    },
                )

    async def delete_deepcourse(self, user_id: str, deepcourse_id: str):
        """Delete complete deep course for a given user with associated documents."""
        async with self.engine.begin() as conn:
            await conn.execute(
                DELETE_DEEPCOURSE, {"id": deepcourse_id, "google_sub": user_id}
            )

    async def fetch_all_chapters(self, deepcourse_id: str):
        """Fetch all chapters for a given deep course."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                FETCH_ALL_CHAPTERS, {"deep_course_id": deepcourse_id}
            )
            chapters = [dict(row._mapping) for row in result.fetchall()]
        return chapters

    async def fetch_chapter_documents(self, chapter_id: str):
        """Fetch document sessions for a given chapter."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                FETCH_CHAPTER_DOCUMENTS, {"chapter_id": chapter_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def rename_chapter(self, chapter_id: str, title: str):
        """Rename a chapter."""
        async with self.engine.begin() as conn:
            await conn.execute(
                RENAME_CHAPTER, {"title": title, "chapter_id": chapter_id}
            )

    async def delete_chapter(self, chapter_id: str):
        """Delete a chapter."""
        async with self.engine.begin() as conn:
            await conn.execute(DELETE_CHAPTER, {"chapter_id": chapter_id})

    async def get_session_from_document(self, chapter_id: str):
        """Fetch session IDs of documents in a chapter."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                GET_SESSION_FROM_DOCUMENT,
                {"chapter_id": chapter_id},
            )
            return [row[0] for row in result.fetchall()]

    async def delete_document_for_chapter(self, chapter_id: str):
        """Delete all documents associated with a chapter."""
        async with self.engine.begin() as conn:
            await conn.execute(DELETE_DOCUMENTS_BY_CHAPTER, {"chapter_id": chapter_id})

    async def mark_chapter_complete(self, chapter_id: str):
        """Mark a chapter as complete."""
        async with self.engine.begin() as conn:
            await conn.execute(MARK_CHAPTER_COMPLETE, {"chapter_id": chapter_id})

    async def mark_chapter_uncomplete(self, chapter_id: str):
        """Mark a chapter as incomplete."""
        async with self.engine.begin() as conn:
            await conn.execute(MARK_CHAPTER_UNCOMPLETE, {"chapter_id": chapter_id})

    async def change_settings(
        self,
        user_id: str,
        new_given_name: Union[str, None],
        new_niveau_etude: Union[str, None],
        new_notion_token: Union[str, None],
    ):
        """Update user settings."""
        async with self.engine.begin() as conn:
            await conn.execute(
                CHANGE_SETTINGS,
                {
                    "user_id": user_id,
                    "new_given_name": new_given_name,
                    "new_niveau_etude": new_niveau_etude,
                    "new_notion_token": new_notion_token,
                },
            )

    async def login_user(self, email: str):
        """Fetch user by email for login."""
        async with self.engine.begin() as conn:
            result = await conn.execute(LOGIN_USER, {"email": email})
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def signup_user(
        self,
        google_sub: str,
        email: str,
        name: str = "",
        notion_token: str = "",
        study: str = "",
    ):
        """Create new user account."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                SIGNUP_USER,
                {
                    "google_sub": google_sub,
                    "email": email,
                    "created_at": datetime.now(),
                    "name": name,
                    "notion_token": notion_token,
                    "study": study,
                },
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def correct_plain_question(
        self, doc_id: str, id_question: str, is_correct: bool, answer: str
    ):
        """Update correction status of a question in a document."""
        async with self.engine.begin() as conn:
            await conn.execute(
                CORRECT_PLAIN_QUESTION,
                {
                    "doc_id": doc_id,
                    "id_question": id_question,
                    "is_correct": is_correct,
                    "answer": answer,
                },
            )

    async def mark_is_corrected_qcm(self, doc_id: str, question_id: str):
        """Mark a QCM question as corrected in a document."""
        async with self.engine.begin() as conn:
            await conn.execute(
                MARK_IS_CORRECTED_QCM, {"doc_id": doc_id, "id_question": question_id}
            )

    async def get_document_by_id(self, session_id: str):
        """Fetch document content for copilot context by session_id."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                FETCH_DOCUMENT_CONTENT_BY_ID, {"session_id": session_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def get_document_by_session_id(self, session_id: str):
        """Fetch document by session_id."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                FETCH_DOCUMENT_BY_SESSION, {"session_id": session_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None


if __name__ == "__main__":
    import asyncio

    async def main():
        db_manager = DBManager()
        await db_manager.test_db()

    asyncio.run(main())
