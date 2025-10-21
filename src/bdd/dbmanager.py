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
    UPDATE_DOCUMENT_CONTENT
)
from src.config import database_settings
from typing import Union
from src.models import ExerciseOutput, CourseOutput
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

    async def store_deepcourse(self, title: str, sub: str):
        id = str(uuid4())
        async with self.engine.begin() as conn:
            await conn.execute(
                CREATE_DEEPCOURSE,
                {"id": id, "title": title, "google_sub": sub}
            )
        
    async def store_chapter(self, deepcourse_id: str, title: str):
        id = str(uuid4())
        async with self.engine.begin() as conn:
            await conn.execute(
                CREATE_CHAPTER,
                {"id": id, "deepcourse_id": deepcourse_id, "title": title}
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
