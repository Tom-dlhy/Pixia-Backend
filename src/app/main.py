from fastapi import FastAPI
from src.config import app_settings
import uvicorn
from src.app.api import health_router, chat_router,api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title=app_settings.APP_NAME,
        debug=app_settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Routes “racine”
    @app.get("/", tags=["Root"])
    async def root():
        return {"ok": True, "app": app_settings.APP_NAME, "env": app_settings.ENV}

    # Routes API
    app.include_router(api_router, prefix="/api")
    return app

app = create_app()

def dev_server():
    """Entrypoint DEV (hot reload) – source de vérité."""
    uvicorn.run(
        "src.app.main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=True,
    )

def prod_server():
    """Entrypoint PROD (sans reload)."""
    uvicorn.run(
        "src.app.main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=False,
    )