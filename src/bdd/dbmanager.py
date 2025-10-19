from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text, create_engine
from google.adk.sessions import DatabaseSessionService
from src.bdd.schema_sql import Base
from src.bdd.query import CHECK_TABLES, CLEAR_ALL_TABLES, DROP_ALL_TABLES, FETCH_ALL_CHATS, RENAME_SESSION, CREATE_SESSION_TITLE
from src.config import database_settings


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
    async def fetch_all_chats(self, user_id: str):
        """Récupère toutes les sessions de chat pour un utilisateur donné."""
        async with self.engine.begin() as conn:
            result = await conn.execute(FETCH_ALL_CHATS, {"user_id": user_id})
            sessions = [dict(row._mapping) for row in result.fetchall()]
        return sessions
    
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
