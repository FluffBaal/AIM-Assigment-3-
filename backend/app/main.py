from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
from slowapi.errors import RateLimitExceeded

from app.api import router
from app.core.config import settings
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.middleware.rate_limiter import (
    limiter,
    api_key_limiter,
    rate_limit_exceeded_handler
)
from app.middleware.request_validator import RequestValidator
from app.middleware.monitoring import MonitoringMiddleware, performance_monitor
from app.middleware.error_tracking import ErrorTrackingMiddleware

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up RAG Chat Application...")
    # Start performance monitoring
    await performance_monitor.start_monitoring()
    yield
    # Shutdown
    logger.info("Shutting down RAG Chat Application...")
    # Stop performance monitoring
    await performance_monitor.stop_monitoring()

app = FastAPI(
    title="RAG Chat Application",
    description="A chat application with PDF upload and RAG capabilities",
    version="0.1.0",
    lifespan=lifespan
)

# Add rate limiter state to app
app.state.limiter = limiter
app.state.api_key_limiter = api_key_limiter

# Add request validator middleware
app.add_middleware(RequestValidator)

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

# Add error tracking middleware
app.add_middleware(ErrorTrackingMiddleware)

# Add caching middleware
# Note: Caching middleware not added to avoid middleware conflicts during testing

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "RAG Chat Application API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}