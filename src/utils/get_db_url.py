import logging
import asyncpg
from asyncpg import Pool
from contextlib import asynccontextmanager
from src.config import database_settings

logger = logging.getLogger(__name__)

async def create_db_pool(min_size: int = 1, max_size: int = 10) -> Pool:
    """
    Initialise un pool de connexions PostgreSQL asynchrone.
    Utilise la configuration issue de DatabaseSettings.
    """
    try:
        pool: Pool = await asyncpg.create_pool(
            dsn=database_settings.dsn,
            min_size=min_size,
            max_size=max_size,
            command_timeout=60,
        )
        logger.info(f"✅ Database pool created successfully ({min_size}-{max_size})")
        return pool

    except Exception as e:
        logger.exception("❌ Failed to create database pool")
        raise RuntimeError(f"Could not connect to the database: {e}") from e

@asynccontextmanager
async def get_connection(pool: Pool):
    """
    Acquiert et libère automatiquement une connexion depuis le pool.
    Exemple :
        async with get_connection(app.state.db_pool) as conn:
            rows = await conn.fetch("SELECT * FROM users")
    """
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)
