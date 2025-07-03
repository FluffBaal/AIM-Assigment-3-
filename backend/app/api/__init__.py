from fastapi import APIRouter

from app.api.endpoints import upload, chat, health

router = APIRouter()

router.include_router(upload.router, prefix="/upload", tags=["upload"])
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(health.router, prefix="/health", tags=["health"])