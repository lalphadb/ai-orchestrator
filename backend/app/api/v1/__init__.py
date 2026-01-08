"""API v1 routes"""
from fastapi import APIRouter

from .auth import router as auth_router
from .chat import router as chat_router
from .conversations import router as conversations_router
from .system import router as system_router
from .tools import router as tools_router
from .learning import router as learning_router

# Router principal
router = APIRouter(prefix="/api/v1")

# Inclure tous les sous-routers
router.include_router(auth_router, tags=["Authentication"])
router.include_router(chat_router, tags=["Chat"])
router.include_router(conversations_router, tags=["Conversations"])
router.include_router(system_router, tags=["System"])
router.include_router(tools_router, tags=["Tools"])
router.include_router(learning_router, tags=["Learning"])

__all__ = ["router"]
