from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom handler for rate limit exceeded errors"""
    response = JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "type": "rate_limit_error",
            "status_code": 429
        }
    )
    response.headers["Retry-After"] = str(60)  # Suggest retry after 60 seconds
    response.headers["X-RateLimit-Limit"] = str(request.state.view_rate_limit)
    response.headers["X-RateLimit-Remaining"] = "0"
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
    return response

# API key based rate limiting
def get_api_key_from_request(request: Request) -> str:
    """Extract API key from request headers for rate limiting"""
    api_key = request.headers.get("X-API-Key", "")
    if api_key:
        # Use last 8 characters of API key for rate limiting
        # This provides some anonymity while still allowing per-key limits
        return f"api_key:{api_key[-8:]}"
    return get_remote_address(request)

# Create a limiter for API key based rate limiting
api_key_limiter = Limiter(key_func=get_api_key_from_request)

# Rate limit configurations
RATE_LIMITS = {
    "default": "100/minute",
    "upload": "10/minute",
    "chat": "50/minute",
    "health": "1000/minute"
}