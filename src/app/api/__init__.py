from fastapi import APIRouter
from .health import router as health_router
from .chat import router as chat_router
from .google import router as google_router
from .files import router as files_router
from .fetchallchats import router as fetchallchats_router
from .fetchchat import router as fetchchat_router
from .renamechat import router as renamechat_router
from .deletechat import router as deletechat_router
from .renamechapter import router as renamechapter_router
from .deletechapter import router as deletechapter_router
from .correctplainquestion import router as correctplainquestion_router
from .markchaptercomplete import router as markchaptercomplete_router
from .markchapteruncomplete import router as markchapteruncomplete_router
from .changesettings import router as changesettings_router
from .markcorrectedQCM import router as markcorrectedQCM_router
from .signup import router as signup_router
from .login import router as login_router
from .test import router as test_router
from .signup import router as signup_router
from .login import router as login_router
from .test import router as test_router


api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(google_router)
api_router.include_router(files_router)
api_router.include_router(fetchallchats_router)
api_router.include_router(fetchchat_router)
api_router.include_router(renamechat_router)
api_router.include_router(deletechat_router)
api_router.include_router(renamechapter_router)
api_router.include_router(deletechapter_router)
api_router.include_router(correctplainquestion_router)
api_router.include_router(markchaptercomplete_router)
api_router.include_router(markchapteruncomplete_router)
api_router.include_router(changesettings_router)
api_router.include_router(markcorrectedQCM_router)
api_router.include_router(signup_router)
api_router.include_router(login_router)
api_router.include_router(test_router)


__all__ = [
    "health_router",
    "chat_router",
    "api_router",
    "google_router",
    "files_router",
    "fetchallchats_router",
    "fetchchat_router",
    "renamechat_router",
    "deletechat_router",
    "renamechapter_router",
    "deletechapter_router",
    "correctplainquestion_router",
    "markchaptercomplete_router",
    "markchapteruncomplete_router"
    "changesettings_router",
    "markcorrectedQCM_router",
    "signup_router",
    "login_router",
    "test_router"
]

