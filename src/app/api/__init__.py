from fastapi import APIRouter
from .health import router as health_router
from .chat import router as chat_router
from .google import router as google_router
from .fetchallchats import router as fetchallchats_router
from .renamechat import router as renamechat_router
from .deletechat import router as deletechat_router
from .renamechapter import router as renamechapter_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(google_router)
api_router.include_router(fetchallchats_router)
api_router.include_router(renamechat_router)
api_router.include_router(deletechat_router)
api_router.include_router(renamechapter_router)

__all__ = [
    "health_router",
    "chat_router",
    "api_router",
    "google_router",
    "fetchallchats_router",
    "renamechat_router",
    "deletechat_router",
    "renamechapter_router"
]