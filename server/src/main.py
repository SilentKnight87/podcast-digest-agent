from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router_v1
from src.config.logging_config import logger
from src.config.settings import settings

# --- FastAPI App Setup ---
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and deployment readiness."""
    return {"status": "healthy", "service": settings.APP_NAME, "version": "0.1.0"}

# Explicit CORS preflight handler for debugging
@app.options("/{full_path:path}")
async def handle_options(full_path: str):
    """Handle OPTIONS requests for CORS preflight."""
    return {"message": "OK"}

# Add logging middleware to debug CORS issues
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {process_time:.4f}s")
    
    return response


# Include API routers
app.include_router(api_router_v1)

# Log application startup
logger.info(f"{settings.APP_NAME} is up and running!")
