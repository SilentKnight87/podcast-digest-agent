from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Path as FastApiPath, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
# from pydantic import BaseModel # BaseModel is now in api_models
from typing import List, Dict
import os # Keep os import

from src.config.settings import settings
from src.models.api_models import (
    ApiConfigResponse, ConfigOption, 
    ProcessUrlRequest, ProcessUrlResponse, 
    TaskStatusResponse, MessageResponse
)
from src.core import task_manager # Import the task manager
from src.core.connection_manager import manager as ws_manager # Import the WebSocket connection manager

import logging # Keep logging import
from pathlib import Path # Keep Path import

# Import agents using absolute paths from src
# from src.agents.transcript_fetcher import TranscriptFetcher # Keep for later
# from src.agents.summarizer import SummarizerAgent # Keep for later
# from src.agents.synthesizer import SynthesizerAgent # Keep for later
# from src.agents.audio_generator import AudioGenerator # Keep for later

# Import runner using absolute paths from src
# from src.runners.pipeline_runner import PipelineRunner # Keep for later

# Import utils using absolute paths from src
# from src.utils.input_processor import get_valid_video_ids # Keep for later
# from src.utils.gcloud_utils import check_gcloud_adc # Function defined locally
# from src.utils.init_utils import initialize_adk_and_clients # Function defined locally

# --- FastAPI App Setup ---
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- API Router V1 ---
api_router_v1 = APIRouter(prefix=settings.API_V1_STR)

@api_router_v1.get("/config", response_model=ApiConfigResponse)
async def get_api_config():
    return ApiConfigResponse(
        available_tts_voices=[ConfigOption(**voice) for voice in settings.AVAILABLE_TTS_VOICES],
        available_summary_lengths=[ConfigOption(**length) for length in settings.AVAILABLE_SUMMARY_LENGTHS],
        available_audio_styles=[ConfigOption(**style) for style in settings.AVAILABLE_AUDIO_STYLES],
    )

@api_router_v1.post("/process_youtube_url", response_model=ProcessUrlResponse, status_code=202)
async def process_youtube_url_endpoint(
    request: ProcessUrlRequest,
    background_tasks: BackgroundTasks
):
    """
    Accepts a YouTube URL and optional configurations, then triggers the backend processing pipeline.
    Returns a task ID for status polling.
    """
    # Actual video detail fetching and extensive validation would go here or in a background task.
    # For now, task_manager.add_new_task simulates some of this.
    
    task_details = task_manager.add_new_task(request.youtube_url, request)

    # Placeholder for actual background processing function
    # background_tasks.add_task(run_processing_pipeline, task_details["task_id"], request)
    # logger.info(f"Task {task_details['task_id']} added to background processing for URL: {request.youtube_url}")
    
    # Notify about new task, could be useful for admin or if WS connection established before POST response
    # await ws_manager.broadcast_to_task(task_details["task_id"], task_manager.get_task_status(task_details["task_id"]).dict()) 
    return ProcessUrlResponse(**task_details)

@api_router_v1.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status_endpoint(task_id: str = FastApiPath(..., title="The ID of the task to get status for")):
    """
    Returns the detailed status of a processing task.
    """
    status = task_manager.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@api_router_v1.websocket("/ws/status/{task_id}")
async def websocket_status_endpoint(websocket: WebSocket, task_id: str = FastApiPath(..., title="Task ID to subscribe for status updates")):
    await ws_manager.connect(websocket, task_id)
    logger.info(f"WebSocket client connected for task_id: {task_id}")

    # Send initial status if task exists
    initial_status = task_manager.get_task_status(task_id)
    if initial_status:
        try:
            await websocket.send_json(initial_status.dict())
        except WebSocketDisconnect:
            # Client might disconnect immediately after connect before we send initial status
            ws_manager.disconnect(websocket, task_id)
            logger.warning(f"WebSocket client for task {task_id} disconnected before initial status send.")
            return # Exit if disconnected
        except Exception as e:
            logger.error(f"Error sending initial status to WebSocket for task {task_id}: {e}")
            # ws_manager.disconnect(websocket, task_id) # Disconnect on other errors too
            # return
    else:
        # If task doesn't exist yet, or if we want to send a specific message:
        # await websocket.send_json({"task_id": task_id, "status": "not_found_or_pending_creation"})
        logger.warning(f"Task {task_id} not found when WebSocket connected. Client will wait for updates.")

    try:
        while True:
            # Keep the connection alive. The client primarily listens.
            # Server pushes updates via task_manager -> ws_manager.broadcast_to_task
            # We can implement a simple ping/pong or just wait for data if client sends any (though not expected here)
            data = await websocket.receive_text() # Or receive_json if client is expected to send structured data
            # logger.debug(f"Received from WebSocket for task {task_id}: {data}")
            # For this use case, server pushes, client listens. So, we might not expect client messages.
            # If client sends "ping", server could reply "pong"
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for task_id: {task_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for task {task_id}: {e}", exc_info=True)
    finally:
        ws_manager.disconnect(websocket, task_id)
        logger.info(f"Cleaned up WebSocket connection for task_id: {task_id}")

# Placeholder for the actual pipeline runner function
# async def run_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
#     logger.info(f"Background task started for {task_id}")
#     try:
#         # Simulate some processing steps
#         import time
#         time.sleep(5) # Simulate transcript fetching
#         task_manager.update_agent_status(task_id, "transcript-fetcher", "completed", progress=100)
#         task_manager.update_task_processing_status(task_id, "processing", progress=25, current_agent_id="summarizer-agent")
        
#         time.sleep(10) # Simulate summarization
#         task_manager.update_agent_status(task_id, "summarizer-agent", "completed", progress=100)
#         task_manager.update_task_processing_status(task_id, "processing", progress=50, current_agent_id="audio-generator")

#         time.sleep(10) # Simulate audio generation
#         task_manager.update_agent_status(task_id, "audio-generator", "completed", progress=100)
#         task_manager.update_task_processing_status(task_id, "processing", progress=75, current_agent_id="output-player")

#         # Simulate creating an audio file
#         audio_filename = f"{task_id}_digest.mp3"
#         audio_file_path = Path(settings.OUTPUT_AUDIO_DIR) / audio_filename
#         with open(audio_file_path, "w") as f: # Create a dummy file
#             f.write("This is a dummy audio file.")
        
#         audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}" # Construct the URL based on actual API path

#         task_manager.set_task_completed(task_id, "This is a mock summary.", audio_url)
#         logger.info(f"Background task {task_id} completed successfully.")

#     except Exception as e:
#         logger.error(f"Error in background task {task_id}: {e}", exc_info=True)
#         task_manager.set_task_failed(task_id, str(e))

app.include_router(api_router_v1)

# --- API Endpoint for Serving Audio (from output_audio directory) ---
@app.get(f"{settings.API_V1_STR}/audio/{{filename}}", response_class=FileResponse, tags=["Audio"], name="get_audio_file")
async def get_audio_file(filename: str):
    """
    Serves a generated audio file.
    Ensure the filename is sanitized to prevent directory traversal.
    """
    # Basic sanitization
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = Path(settings.OUTPUT_AUDIO_DIR) / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    
    # Ensure the file is within the designated audio directory
    try:
        # Resolve both paths to their absolute form to prevent traversal attacks
        base_dir_resolved = Path(settings.OUTPUT_AUDIO_DIR).resolve(strict=True)
        file_path_resolved = file_path.resolve(strict=True)
        
        # Check if the resolved file_path is a child of base_dir_resolved
        if base_dir_resolved not in file_path_resolved.parents and base_dir_resolved != file_path_resolved.parent:
             raise HTTPException(status_code=403, detail="Access to this file is forbidden.")

    except FileNotFoundError: # If strict=True and path doesn't exist
        raise HTTPException(status_code=404, detail="Audio file not found or invalid path.")
    except Exception as e:
        logger.error(f"Error resolving audio file path: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while accessing file.")

    return FileResponse(file_path, media_type="audio/mpeg", filename=filename)

# --- Logging Setup (can be kept or moved to a dedicated logging config file) ---
LOG_FILE = os.getenv('LOG_FILE') 
log_handler = logging.FileHandler(LOG_FILE) if LOG_FILE and Path(LOG_FILE).parent.exists() else logging.StreamHandler()
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] [%(module)s:%(lineno)d] - %(message)s',
    handlers=[log_handler]
)
logger = logging.getLogger(__name__)

logger.info(f"{settings.APP_NAME} API started. Debug mode: {settings.DEBUG}")
logger.info(f"Output audio directory: {settings.OUTPUT_AUDIO_DIR}")
logger.info(f"Input directory: {settings.INPUT_DIR}")
if settings.GOOGLE_APPLICATION_CREDENTIALS:
    logger.info(f"Using Google Credentials from: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
else:
    logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set. Google Cloud services might not be available.")


# Placeholder for history endpoint (to be implemented)
# @api_router_v1.get("/history", response_model=TaskHistoryResponse)
# async def get_task_history_endpoint(limit: int = 10, offset: int = 0):
#     # Logic to fetch from task_manager or a persistent store
#     pass

# To run the app (example):
# uvicorn src.main:app --reload 