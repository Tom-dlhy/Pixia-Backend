from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os
import asyncio
from src.config import app_settings
from src.utils import create_db_pool
from src.app.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Désactiver les loggers verbeux des dépendances
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("google.genai.models").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google.adk").setLevel(logging.WARNING)


def create_app() -> FastAPI:
    """Crée et configure l'application FastAPI."""
    app = FastAPI(
        title=app_settings.APP_NAME,
        debug=app_settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "ok": True,
            "app": app_settings.APP_NAME,
            "env": app_settings.ENV,
        }

    app.include_router(api_router, prefix="/api")

    # @app.on_event("startup")
    # async def on_startup():
    #     """Initialise les ressources au démarrage de l'application."""
    #     logger.info("Starting FastAPI application...")
    #     app.state.db_pool = await create_db_pool()
    #     logger.info("Database pool initialized and ready.")

    @app.on_event("startup")
    async def on_startup():
        logger.info("Starting FastAPI application...")

        if os.getenv("SKIP_DB_INIT", "false").lower() == "true":
            app.state.db_pool = None
            logger.warning("DB init skipped (SKIP_DB_INIT=true).")
            return

        try:
            timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "5"))
            app.state.db_pool = await asyncio.wait_for(
                create_db_pool(), timeout=timeout
            )
            logger.info("Database pool initialized and ready.")
        except Exception as e:
            logger.exception("DB init failed; starting without DB.")
            app.state.db_pool = None

    @app.on_event("shutdown")
    async def on_shutdown():
        """Ferme proprement les ressources avant l'arrêt."""
        logger.info("Shutting down FastAPI application...")
        await app.state.db_pool.close()
        logger.info("Database pool closed successfully.")

    return app


app = create_app()


def dev_server():
    """Lance le serveur en mode développement (reload activé)."""
    uvicorn.run(
        "src.app.main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=True,
        log_level="info",
    )


def prod_server():
    """Lance le serveur en mode production (sans reload)."""
    uvicorn.run(
        "src.app.main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    mode = "development" if app_settings.DEBUG else "production"
    logger.info(f"Running FastAPI in {mode} mode")
    if app_settings.DEBUG:
        dev_server()
    else:
        prod_server()
