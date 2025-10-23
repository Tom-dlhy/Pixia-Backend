from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from google.adk.sessions import DatabaseSessionService
from src.bdd.schema_sql import Base
from src.bdd.query import (
    CHECK_TABLES, 
    CLEAR_ALL_TABLES,
    DROP_ALL_TABLES, 
    FETCH_ALL_CHATS, 
    RENAME_SESSION,
    CREATE_SESSION_TITLE, 
    STORE_BASIC_DOCUMENT, 
    RENAME_CHAT, 
    DELETE_SESSION_TITLE, 
    DELETE_DOCUMENTS,
    RENAME_CHAPTER, 
    DELETE_CHAPTER,
    MARK_CHAPTER_COMPLETE,
    MARK_CHAPTER_UNCOMPLETE,
    CHANGE_SETTINGS,
    GET_SESSION_FROM_DOCUMENT,
    DELETE_DOCUMENTS_BY_CHAPTER,
    LOGIN_USER,
    SIGNUP_USER,
    CORRECT_PLAIN_QUESTION,
    MARK_IS_CORRECTED_QCM,
    CREATE_CHAPTER,
    CREATE_DEEPCOURSE,
    UPDATE_DOCUMENT_CONTENT,
    FETCH_DOCUMENT_BY_SESSION,
    GET_DEEPCOURSE_AND_CHAPTER_FROM_ID
)
from src.config import database_settings
from typing import Union,List,Dict,Any
from src.models import ExerciseOutput, CourseOutput, DeepCourseOutput
from datetime import datetime
import json
from uuid import uuid4
from typing import Optional


# =========================================================
# CONFIGURATION DES DSN
# =========================================================
DATABASE_URL_SYNC = database_settings.dsn

# 🔧 Conversion propre vers un DSN async
if "+asyncpg" not in DATABASE_URL_SYNC:
    if "+psycopg2" in DATABASE_URL_SYNC:
        DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace("+psycopg2", "+asyncpg")
    else:
        DATABASE_URL_ASYNC = DATABASE_URL_SYNC.replace("postgresql://", "postgresql+asyncpg://")
else:
    DATABASE_URL_ASYNC = DATABASE_URL_SYNC

print("🧩 DSN async utilisé :", DATABASE_URL_ASYNC)


# =========================================================
# CLASSE DBManager ASYNCHRONE
# =========================================================
class DBManager:
    """
    Gestionnaire asynchrone de base de données :
    - moteur async pour toutes les requêtes métier
    - create_db() qui utilise temporairement ADK (sync) pour créer toutes les tables
    """

    def __init__(self):
        # 🔹 moteur async standard pour le backend
        self.engine = create_async_engine(DATABASE_URL_ASYNC, echo=False, future=True)
        self.SessionLocal = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        print("⚙️  Moteur async initialisé (backend).")

    # -----------------------------------------------------
    # CRÉATION COMPLÈTE DE LA BASE VIA ADK
    # -----------------------------------------------------
    async def create_db(self):
        """
        Initialise la base complète :
        - Utilise ADK (sync) pour créer ses tables core (sessions, events, states)
        - Crée ensuite les tables métier sur le même moteur
        - Recrée ensuite le moteur async du backend
        """
        print("🚀 Initialisation complète de la base via ADK...")

        # 1️⃣ Lancer ADK (sync) → crée ses propres tables
        adk_service = DatabaseSessionService(db_url=DATABASE_URL_SYNC)
        adk_engine = adk_service.db_engine

        # 2️⃣ Créer les tables métiers sur le moteur ADK
        Base.metadata.create_all(bind=adk_engine)
        print("✅ Tables ADK + tables métiers créées (via moteur sync ADK).")

        # 3️⃣ Recréer le moteur async pour le backend
        self.engine = create_async_engine(DATABASE_URL_ASYNC, echo=False, future=True)
        self.SessionLocal = async_sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )
        print("🔄 Moteur async restauré pour le backend.")

    # -----------------------------------------------------
    # CONTEXT MANAGER ASYNC (FastAPI compatible)
    # -----------------------------------------------------
    async def get_db(self):
        """Context manager asynchrone pour ouvrir une session DB."""
        async with self.SessionLocal() as session:
            yield session

    # -----------------------------------------------------
    # UTILITAIRES ASYNC
    # -----------------------------------------------------
    async def clear_tables(self):
        """Vide toutes les tables sans les supprimer."""
        async with self.engine.begin() as conn:
            await conn.execute(CLEAR_ALL_TABLES)
        print("🧹 Tables vidées.")

    async def clear_db(self):
        """Supprime toutes les tables (ADK + métiers)."""
        async with self.engine.begin() as conn:
            await conn.execute(DROP_ALL_TABLES)
        print("💣 Toutes les tables supprimées.")

    async def test_db(self):
        """Teste la connexion et liste les tables existantes."""
        async with self.engine.begin() as conn:
            result = await conn.execute(CHECK_TABLES)
            tables = [row[0] for row in result.fetchall()]
        print("📋 Tables existantes :", tables)
        return tables

    # -----------------------------------------------------
    # REQUÊTES MÉTIER ASYNC
    # -----------------------------------------------------

    # Route fetchallchats
    async def fetch_all_chats(self, user_id: str):
        """Récupère toutes les sessions de chat pour un utilisateur donné."""
        async with self.engine.begin() as conn:
            result = await conn.execute(FETCH_ALL_CHATS, {"user_id": user_id})
            sessions = [dict(row._mapping) for row in result.fetchall()]
        return sessions
    
    # Route chat
    
    async def rename_session(self, title:str, session_id:str):
        """Renomme une session de chat donnée."""
        async with self.engine.begin() as conn:
            await conn.execute(
                RENAME_SESSION,
                {"title": title, "session_id": session_id}
            )
    
    async def create_session_title(self, session_id:str, title:str, is_deepcourse:bool=False):
        """Crée un titre de session."""
        async with self.engine.begin() as conn:
            await conn.execute(
                CREATE_SESSION_TITLE,
                {"session_id": session_id, "title": title, "is_deepcourse": is_deepcourse}
            )

    async def store_basic_document(self, content:Union[ExerciseOutput, CourseOutput], session_id:str, sub:str, chapter_id:Optional[str]=None):
        """Stocke un document (exercice ou cours) associé à une session."""
        type = "exercise" if isinstance(content, ExerciseOutput) else "course" if isinstance(content, CourseOutput) else "eval"
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
                {"id": document_id, "google_sub": sub, "session_id": session_id, "chapter_id": chapter_id, "document_type": type, "contenu": contenu_json, "created_at": created_at, "updated_at": updated_at}
            )

    async def delete_document(self, document_id: str):
        """Supprime un document donné."""
        async with self.engine.begin() as conn:
            await conn.execute(
                DELETE_DOCUMENTS,
                {"document_id": document_id}
            )

    async def update_document(self, document_id: str, new_content: Union[ExerciseOutput, CourseOutput]):
        """Met à jour le contenu d'un document donné."""
        contenu_json = json.dumps(
            new_content.model_dump() if hasattr(new_content, "model_dump") else new_content
        )
        async with self.engine.begin() as conn:
            await conn.execute(
                UPDATE_DOCUMENT_CONTENT,
                {"id": document_id, "contenu": contenu_json}
            )

    async def get_deepcourse_and_chapter_with_id(self,deepcourse_id):
        async with self.engine.begin() as conn:
            result = await conn.execute(
                GET_DEEPCOURSE_AND_CHAPTER_FROM_ID,
                {"deepcourse_id": deepcourse_id}
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
        """Store un chapitre d'un deepcourse"""

        now = datetime.now()

        async with self.engine.begin() as conn:
            await conn.execute(
                CREATE_CHAPTER,
                {
                    "id": chapter_id,
                    "deep_course_id": deepcourse_id,
                    "titre": title,
                    "is_complete": False
                }
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
                            "updated_at": now
                        }
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
                            "updated_at": now
                        }
                    )
            evaluation_json = json.dumps(
                    evaluation.model_dump() if hasattr(evaluation, "model_dump") else evaluation
                )
            await conn.execute(
                        STORE_BASIC_DOCUMENT,
                        {
                            "id": evaluation.id,
                            "google_sub": user_id,
                            "session_id": session_evaluation,
                            "chapter_id": chapter_id,
                            "document_type": "evaluation",
                            "contenu": evaluation_json,
                            "created_at": now,
                            "updated_at": now
                        }
                    )

    async def store_deepcourse(self, user_id: str, 
                                content: DeepCourseOutput, 
                                dict_session: List[Dict[str, str]]):
        """
        Stocke un deepcourse complet :
        1. Crée le deepcourse
        2. Pour chaque chapitre : crée le chapitre et stocke ses 3 documents (exercice, cours, évaluation)
        
        Args:
            user_id: ID utilisateur (google_sub)
            content: Objet DeepCourseOutput avec tous les chapitres
            dict_session: Liste de dicts avec structure:
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
                {
                    "id": deepcourse_id,
                    "titre": content.title,
                    "google_sub": user_id
                }
            )
            
            for idx, chapter in enumerate(content.chapters):
                chapter_id = chapter.id_chapter or str(uuid4())
                
                await conn.execute(
                    CREATE_CHAPTER,
                    {
                        "id": chapter_id,
                        "deep_course_id": deepcourse_id,
                        "titre": chapter.title,
                        "is_complete": False
                    }
                )
                
                chapter_sessions = dict_session[idx]
                session_exercise = chapter_sessions["session_id_exercise"]
                session_course = chapter_sessions["session_id_course"]
                session_evaluation = chapter_sessions["session_id_evaluation"]
                
                now = datetime.now()
                
                exercise_id = chapter.exercice.id or str(uuid4())
                exercise_json = json.dumps(
                    chapter.exercice.model_dump() if hasattr(chapter.exercice, "model_dump") else chapter.exercice
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
                        "updated_at": now
                    }
                )
                
                course_id = chapter.course.id or str(uuid4())
                course_json = json.dumps(
                    chapter.course.model_dump() if hasattr(chapter.course, "model_dump") else chapter.course
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
                        "updated_at": now
                    }
                )
                
                evaluation_id = chapter.evaluation.id or str(uuid4())
                evaluation_json = json.dumps(
                    chapter.evaluation.model_dump() if hasattr(chapter.evaluation, "model_dump") else chapter.evaluation
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
                        "updated_at": now
                    }
                )
        

    async def rename_chat(self, session_id: str, title: str):
        """Renomme une session de chat donnée."""
        async with self.engine.begin() as conn:
            await conn.execute(
                RENAME_CHAT,
                {"title": title, "session_id": session_id}
            )

    async def delete_chat(self, session_id: str):
        """Supprime une session de chat donnée."""
        async with self.engine.begin() as conn:
            await conn.execute(
                DELETE_SESSION_TITLE,
                {"session_id": session_id}
            )
            await conn.execute(
                DELETE_DOCUMENTS,
                {"session_id": session_id}
            )
        
    async def rename_chapter(self, chapter_id: str, title: str):
        """Renomme un chapitre donné."""
        # Implémentation fictive (à adapter selon le schéma réel)
        async with self.engine.begin() as conn:
            await conn.execute(
                RENAME_CHAPTER,
                {"title": title, "chapter_id": chapter_id}
            )

    async def delete_chapter(self, chapter_id: str):
        """Supprime un chapitre donné."""
        # Implémentation fictive (à adapter selon le schéma réel)
        async with self.engine.begin() as conn:
            await conn.execute(
                DELETE_CHAPTER,
                {"chapter_id": chapter_id}
            )

    async def get_session_from_document(self, chapter_id: str):
        """Récupère les session_id des documents ayant ce chapter_id."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                GET_SESSION_FROM_DOCUMENT,
                {"chapter_id": chapter_id},
            )
            return [row[0] for row in result.fetchall()]
        
    async def delete_document_for_chapter(self, chapter_id: str):
        """Supprime les documents associés à un chapitre donné."""
        async with self.engine.begin() as conn:
            await conn.execute(
                DELETE_DOCUMENTS_BY_CHAPTER,
                {"chapter_id": chapter_id}
            )

    async def delete_session_title(self, session_id: str):
        """Supprime le titre d'une session donnée."""
        async with self.engine.begin() as conn:
            await conn.execute(
                DELETE_SESSION_TITLE,
                {"session_id": session_id}
            )

    async def mark_chapter_complete(self, chapter_id: str):
        """Marque un chapitre comme complété pour un utilisateur donné."""
        # Implémentation fictive (à adapter selon le schéma réel)
        async with self.engine.begin() as conn:
            await conn.execute(
                MARK_CHAPTER_COMPLETE,
                {"chapter_id": chapter_id}
            )
    
    async def mark_chapter_uncomplete(self, chapter_id: str):
        """Marque un chapitre comme non complété pour un utilisateur donné."""
        # Implémentation fictive (à adapter selon le schéma réel)
        async with self.engine.begin() as conn:
            await conn.execute(
                MARK_CHAPTER_UNCOMPLETE,
                {"chapter_id": chapter_id}
            )

    async def change_settings(self, user_id: str, new_given_name: Union[str, None], new_family_name: Union[str, None], 
                              new_notion_url: Union[str, None], new_drive_url: Union[str, None]):
        """Change les paramètres utilisateur."""
        # Implémentation fictive (à adapter selon le schéma réel)
        async with self.engine.begin() as conn:
            await conn.execute(
                CHANGE_SETTINGS,
                {
                    "user_id": user_id, 
                    "new_given_name": new_given_name, 
                    "new_family_name": new_family_name, 
                    "new_notion_url": new_notion_url, 
                    "new_drive_url": new_drive_url
                }
            )

    async def login_user(self, email: str):
        async with self.engine.begin() as conn:
            result = await conn.execute(
                LOGIN_USER,
                {"email": email}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def signup_user(self, google_sub: str, email: str, given_name: str = "", family_name: str = ""):
        async with self.engine.begin() as conn:
            result = await conn.execute(
                SIGNUP_USER,
                {"google_sub": google_sub, "email": email, "given_name": given_name, "family_name": family_name}
            )
            return result.fetchone()
        

    async def correct_plain_question(self, doc_id: str, id_question: str, is_correct: bool, answer: str):
        """Met à jour le statut de correction d'une question dans un document."""
        # Implémentation fictive (à adapter selon le schéma réel)
        async with self.engine.begin() as conn:
            await conn.execute(
                CORRECT_PLAIN_QUESTION,
                {"doc_id": doc_id, "id_question": id_question, "is_correct": is_correct, "answer": answer}
            )

    async def mark_is_corrected_qcm(self, doc_id: str, question_id: str):
        """Marque une question QCM comme corrigée dans un document."""
        # Implémentation fictive (à adapter selon le schéma réel)
        async with self.engine.begin() as conn:
            await conn.execute(
                MARK_IS_CORRECTED_QCM,
                {"doc_id": doc_id, "id_question": question_id}
            )

    async def get_document(self, sesssion_id: str):
        """Récupère un document par session_id."""
        async with self.engine.begin() as conn:
            result = await conn.execute(
                FETCH_DOCUMENT_BY_SESSION,
                {"session_id": sesssion_id}
            )
            row = result.fetchone()
            return dict(row._mapping) if row else None

# =========================================================
# SCRIPT DE TEST / DEBUG DIRECT
# =========================================================
if __name__ == "__main__":
    import asyncio

    async def main():
        db_manager = DBManager()
        await db_manager.clear_db()
        await db_manager.create_db()
        await db_manager.test_db()

    asyncio.run(main())
