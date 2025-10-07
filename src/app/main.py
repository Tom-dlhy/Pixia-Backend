from fastapi import FastAPI
from src.app.config import settings
from src.app.api import api_router
import uvicorn

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Routes “racine”
    @app.get("/", tags=["Root"])
    async def root():
        return {"ok": True, "app": settings.APP_NAME, "env": settings.ENV}

    # Routes API
    app.include_router(api_router, prefix="/api")
    return app

app = create_app()

def dev_server():
    """Entrypoint DEV (hot reload) – source de vérité."""
    uvicorn.run(
        "src.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )

def prod_server():
    """Entrypoint PROD (sans reload)."""
    uvicorn.run(
        "src.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
    )