from fastapi import APIRouter
from .health import router as health_router
from .chat import router as chat_router
from .google import router as google_router
from .files import router as files_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(google_router)
api_router.include_router(files_router)


__all__ = ["health_router", "chat_router","api_router", "google_router", "files_router"]
