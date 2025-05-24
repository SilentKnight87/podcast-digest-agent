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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router_v1)

# Log application startup
logger.info(f"{settings.APP_NAME} is up and running!")
