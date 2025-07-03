from fastapi import APIRouter
from typing import Dict

router = APIRouter()

@router.get("/status")
async def health_status() -> Dict[str, str]:
    return {
        "status": "healthy",
        "service": "rag-chat-api"
    }

@router.get("/ready")
async def readiness_check() -> Dict[str, bool]:
    return {
        "database": True,
        "openai": True,
        "storage": True
    }