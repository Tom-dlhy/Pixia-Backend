from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from src.config import app_settings
from src.utils import create_db_pool
from src.app.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

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

    @app.on_event("startup")
    async def on_startup():
        """Initialise les ressources au démarrage de l'application."""
        logger.info("Starting FastAPI application...")
        app.state.db_pool = await create_db_pool()
        logger.info("Database pool initialized and ready.")

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
