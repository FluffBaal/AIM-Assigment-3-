from fastapi import APIRouter

router = APIRouter()

# Import routers after creating the main router to avoid circular imports
from app.api.endpoints import upload, chat, health  # noqa: E402

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(upload.router, prefix="/upload", tags=["upload"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])