from fastapi import APIRouter, Request
from typing import Dict
from backend.app.middleware.rate_limiter import limiter, RATE_LIMITS

router = APIRouter()

@router.get("/status")
@limiter.limit(RATE_LIMITS["health"])
async def health_status(request: Request) -> Dict[str, str]:
    return {
        "status": "healthy",
        "service": "rag-chat-api"
    }

@router.get("/ready")
@limiter.limit(RATE_LIMITS["health"])
async def readiness_check(request: Request) -> Dict[str, bool]:
    return {
        "database": True,
        "openai": True,
        "storage": True
    }