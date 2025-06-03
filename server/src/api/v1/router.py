from fastapi import APIRouter

from src.api.v1.endpoints import audio, config, tasks, debug  # Assuming tasks and audio are created here
from src.config.settings import settings

api_router_v1 = APIRouter(prefix=settings.API_V1_STR)

api_router_v1.include_router(config.router, tags=["Configuration"])
api_router_v1.include_router(tasks.router, tags=["Tasks"])
api_router_v1.include_router(audio.router)  # Tags are already in audio.router
api_router_v1.include_router(debug.router, tags=["Debug"])
