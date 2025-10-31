"""API routes router.

Aggregates all API endpoint routers into a single main router.
"""

from fastapi import APIRouter

from .changesettings import router as changesettings_router
from .chat import router as chat_router
from .correctallquestions import router as correctallquestions_router
from .correctplainquestion import router as correctplainquestion_router
from .deletechapter import router as deletechapter_router
from .deletechat import router as deletechat_router
from .deletedeepcourse import router as deletedeepcourse_router
from .downloadcourse import router as downloadcourse_router
from .fetchallchapters import router as fetchallchapters_router
from .fetchallchats import router as fetchallchats_router
from .fetchalldeepcourses import router as fetchalldeepcourses_router
from .fetchchapterdocuments import router as fetchchapterdocuments_router
from .fetchchat import router as fetchchat_router
from .fetchcourse import router as fetch_course_router
from .fetchexercise import router as fetch_exercise_router
from .health import router as health_router
from .login import router as login_router
from .markchaptercomplete import router as markchaptercomplete_router
from .markchapteruncomplete import router as markchapteruncomplete_router
from .markcorrectedQCM import router as markcorrectedQCM_router
from .renamechapter import router as renamechapter_router
from .renamechat import router as renamechat_router
from .signup import router as signup_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(chat_router)
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
api_router.include_router(fetch_exercise_router)
api_router.include_router(fetch_course_router)
api_router.include_router(fetchalldeepcourses_router)
api_router.include_router(fetchallchapters_router)
api_router.include_router(fetchchapterdocuments_router)
api_router.include_router(correctallquestions_router)
api_router.include_router(downloadcourse_router)

__all__ = [
    "api_router",
    "changesettings_router",
    "chat_router",
    "correctallquestions_router",
    "correctplainquestion_router",
    "deletechapter_router",
    "deletechat_router",
    "deletedeepcourse_router",
    "downloadcourse_router",
    "fetchallchapters_router",
    "fetchallchats_router",
    "fetchalldeepcourses_router",
    "fetchchapterdocuments_router",
    "fetchchat_router",
    "fetch_course_router",
    "fetch_exercise_router",
    "health_router",
    "login_router",
    "markchaptercomplete_router",
    "markchapteruncomplete_router",
    "markcorrectedQCM_router",
    "renamechapter_router",
    "renamechat_router",
    "signup_router",
]

