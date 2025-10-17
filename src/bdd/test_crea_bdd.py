"""
Initialise la base PostgreSQL 'conversations' sur Cloud SQL :
- Crée la base si elle n'existe pas encore.
- Crée toutes les tables ADK via SQLAlchemy.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine.url import make_url
import logging
from src.config import database_settings

settings=database_settings
DB_URL=settings.dsn


# === 2. Fonction pour créer la base si absente ===
def ensure_database_exists(db_url: str, fallback_db: str = "postgres"):
    url = make_url(db_url)
    dbname = url.database
    fallback_url = str(url.set(database=fallback_db))

    try:
        engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            print(f"La base '{dbname}' existe déjà.")
        engine.dispose()
    except OperationalError:
        print(f"La base '{dbname}' n'existe pas...")
        

# === 3. Import du schéma ADK ===
from google.adk.sessions.database_session_service import Base  # <-- utilise ton chemin réel d'import ADK


# === 4. Création complète ===
def initialize_conversations_db():
    print("=== Initialisation de la base de données ADK ===")

    ensure_database_exists(DB_URL)

    print("Connexion à la base et création des tables...")
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)

    print("✅ Base et tables créées avec succès !")
    engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    initialize_conversations_db()