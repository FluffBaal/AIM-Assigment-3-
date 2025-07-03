from fastapi import APIRouter

router = APIRouter()

# Import routers after creating the main router to avoid circular imports
from app.api.endpoints import upload, chat, health, monitoring, errors  # noqa: E402

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(upload.router, prefix="/upload", tags=["upload"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
router.include_router(errors.router, prefix="/errors", tags=["errors"])