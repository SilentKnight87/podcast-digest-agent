from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Path as FastApiPath, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
# from pydantic import BaseModel # BaseModel is now in api_models
from typing import List, Dict
import os # Keep os import
import asyncio
from datetime import datetime, timezone

from src.config.settings import settings
from src.config.logging_config import logger # Import the configured logger
from src.models.api_models import (
    ApiConfigResponse, ConfigOption, 
    ProcessUrlRequest, ProcessUrlResponse, 
    TaskStatusResponse, MessageResponse,
    TaskHistoryResponse, HistoryTaskItem, AudioOutput, SummaryContent, VideoDetails
)
from src.core import task_manager # Import the task manager
from src.core.connection_manager import manager as ws_manager # Import the WebSocket connection manager
from src.api.v1.router import api_router_v1 # Import the v1 API router

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

# Include API routers
app.include_router(api_router_v1)

# Log application startup
logger.info(f"{settings.APP_NAME} is up and running!")

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

    # Add the background task to process the URL
    background_tasks.add_task(run_processing_pipeline, task_details["task_id"], request)
    logger.info(f"Task {task_details['task_id']} added to background processing for URL: {request.youtube_url}")
    
    # Notify about new task through WebSocket (optional)
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

async def run_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """
    Process a YouTube URL through the pipeline of agents.
    This is run as a background task after the API request is accepted.
    
    In a production implementation, this would use actual agents and processing.
    For now, it simulates the processing steps with delays.
    """
    logger.info(f"Background task started for {task_id}")
    try:
        # Update status to processing
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=5, 
            current_agent_id="youtube-node"
        )
        
        # For simulation, we'll assume a YouTube source processing step
        await asyncio.sleep(2)  # simulate some processing time
        logger.info(f"Starting YouTube source processing for task {task_id}")
        
        # Update YouTube source status
        task_manager.update_agent_status(
            task_id, 
            "youtube-node", 
            "running", 
            progress=50,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Add some sample logs to the YouTube source agent
        task_manager.add_agent_log(
            task_id, 
            "youtube-node", 
            "INFO", 
            f"Validated YouTube URL: {request_data.youtube_url}"
        )
        
        # Complete the YouTube source processing
        await asyncio.sleep(2)
        task_manager.update_agent_status(
            task_id, 
            "youtube-node", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Start the transcript fetcher agent
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=15, 
            current_agent_id="transcript-fetcher"
        )
        
        # Update the data flow from YouTube source to transcript fetcher
        task_manager.update_data_flow_status(
            task_id, 
            "youtube-node", 
            "transcript-fetcher", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "youtube-node", 
            "transcript-fetcher", 
            "completed"
        )
        
        # Start the transcript fetcher
        task_manager.update_agent_status(
            task_id, 
            "transcript-fetcher", 
            "running", 
            progress=0,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Simulate transcript fetching work
        for i in range(1, 11):
            await asyncio.sleep(0.5)
            task_manager.update_agent_status(
                task_id, 
                "transcript-fetcher", 
                "running", 
                progress=i * 10
            )
            task_manager.add_agent_log(
                task_id, 
                "transcript-fetcher", 
                "INFO", 
                f"Fetching transcript segments: {i * 10}% complete"
            )
        
        # Complete transcript fetching
        task_manager.update_agent_status(
            task_id, 
            "transcript-fetcher", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Move to summarization
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=30, 
            current_agent_id="summarizer-agent"
        )
        
        # Update the data flow from transcript fetcher to summarizer
        task_manager.update_data_flow_status(
            task_id, 
            "transcript-fetcher", 
            "summarizer-agent", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "transcript-fetcher", 
            "summarizer-agent", 
            "completed"
        )
        
        # Start the summarizer
        task_manager.update_agent_status(
            task_id, 
            "summarizer-agent", 
            "running", 
            progress=0,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Simulate summarization work
        for i in range(1, 11):
            await asyncio.sleep(0.7)
            task_manager.update_agent_status(
                task_id, 
                "summarizer-agent", 
                "running", 
                progress=i * 10
            )
            task_manager.add_agent_log(
                task_id, 
                "summarizer-agent", 
                "INFO", 
                f"Summarizing content: {i * 10}% complete"
            )
        
        # Complete summarization
        task_manager.update_agent_status(
            task_id, 
            "summarizer-agent", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Move to synthesis
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=50, 
            current_agent_id="synthesizer-agent"
        )
        
        # Update the data flow from summarizer to synthesizer
        task_manager.update_data_flow_status(
            task_id, 
            "summarizer-agent", 
            "synthesizer-agent", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "summarizer-agent", 
            "synthesizer-agent", 
            "completed"
        )
        
        # Start the synthesizer
        task_manager.update_agent_status(
            task_id, 
            "synthesizer-agent", 
            "running", 
            progress=0,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Simulate synthesis work
        for i in range(1, 6):
            await asyncio.sleep(0.5)
            task_manager.update_agent_status(
                task_id, 
                "synthesizer-agent", 
                "running", 
                progress=i * 20
            )
            task_manager.add_agent_log(
                task_id, 
                "synthesizer-agent", 
                "INFO", 
                f"Synthesizing dialogue: {i * 20}% complete"
            )
        
        # Complete synthesis
        task_manager.update_agent_status(
            task_id, 
            "synthesizer-agent", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Move to audio generation
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=70, 
            current_agent_id="audio-generator"
        )
        
        # Update the data flow from synthesizer to audio generator
        task_manager.update_data_flow_status(
            task_id, 
            "synthesizer-agent", 
            "audio-generator", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "synthesizer-agent", 
            "audio-generator", 
            "completed"
        )
        
        # Start the audio generator
        task_manager.update_agent_status(
            task_id, 
            "audio-generator", 
            "running", 
            progress=0,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Simulate audio generation work
        for i in range(1, 11):
            await asyncio.sleep(0.6)
            task_manager.update_agent_status(
                task_id, 
                "audio-generator", 
                "running", 
                progress=i * 10
            )
            task_manager.add_agent_log(
                task_id, 
                "audio-generator", 
                "INFO", 
                f"Generating audio: {i * 10}% complete"
            )
        
        # Simulate creating an audio file
        audio_filename = f"{task_id}_digest.mp3"
        audio_file_path = Path(settings.OUTPUT_AUDIO_DIR) / audio_filename
        with open(audio_file_path, "w") as f:  # Create a dummy file
            f.write("This is a dummy audio file.")
        
        # Complete audio generation
        task_manager.update_agent_status(
            task_id, 
            "audio-generator", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Move to output player
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=90, 
            current_agent_id="ui-player"
        )
        
        # Update the data flow from audio generator to output player
        task_manager.update_data_flow_status(
            task_id, 
            "audio-generator", 
            "ui-player", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "audio-generator", 
            "ui-player", 
            "completed"
        )
        
        # Start the output player agent
        task_manager.update_agent_status(
            task_id, 
            "ui-player", 
            "running", 
            progress=50,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Complete output player
        await asyncio.sleep(1)
        task_manager.update_agent_status(
            task_id, 
            "ui-player", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Construct the URL for the audio file
        audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}"
        
        # Mark the task as completed
        summary = "In this video, the presenter discusses the key features of the new product " + \
                 "including improved performance, enhanced security, and better user experience. " + \
                 "The product will be available starting next month with a promotional discount " + \
                 "for early adopters. Reviews from beta testers have been overwhelmingly positive."
                 
        task_manager.set_task_completed(task_id, summary, audio_url)
        logger.info(f"Background task {task_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error in background task {task_id}: {e}", exc_info=True)
        task_manager.set_task_failed(task_id, str(e))

@api_router_v1.get("/history", response_model=TaskHistoryResponse)
async def get_task_history_endpoint(
    limit: int = 10, 
    offset: int = 0
):
    """
    Returns a paginated list of completed tasks with their summaries and audio links.
    """
    # Validate input parameters
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be a positive integer")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be a non-negative integer")
    
    # Cap the maximum limit to avoid excessive response sizes
    max_limit = 100
    if limit > max_limit:
        limit = max_limit
    
    # Filter tasks to only include completed ones
    completed_tasks = [
        task for task_id, task in task_manager._tasks_store.items()
        if task.processing_status.status == "completed"
    ]
    
    # Sort tasks by completion time (newest first)
    # Assuming completed tasks have processing_status.estimated_end_time set
    completed_tasks.sort(
        key=lambda task: task.processing_status.estimated_end_time or "", 
        reverse=True
    )
    
    # Apply pagination
    total_tasks = len(completed_tasks)
    paginated_tasks = completed_tasks[offset:offset+limit]
    
    # Convert TaskStatusResponse objects to HistoryTaskItem objects
    history_items = []
    for task in paginated_tasks:
        # Extract duration information
        processing_duration = "Unknown"
        if task.processing_status.start_time and task.processing_status.estimated_end_time:
            # In a real implementation, calculate actual duration from timestamps
            # For now, use the elapsed_time if available
            processing_duration = task.processing_status.elapsed_time or "Unknown"
        
        # Create AudioOutput object
        audio_output = None
        if task.audio_file_url:
            # In a real implementation, get actual file size and duration
            # For now, use placeholder values
            audio_output = AudioOutput(
                url=task.audio_file_url,
                duration="00:03:00",  # Placeholder
                file_size="3.0MB"     # Placeholder
            )
        
        # Create SummaryContent object
        summary = None
        if task.summary_text:
            # In a real implementation, parse the summary text to extract these elements
            # For now, use the summary text as the title and create placeholder data
            summary = SummaryContent(
                title=f"Summary: {task.video_details.title if task.video_details else 'Unknown'}",
                host=task.video_details.channel_name if task.video_details else "Unknown",
                main_points=["Point extracted from summary"],
                highlights=["Highlight extracted from summary"],
                key_quotes=["Quote extracted from summary"]
            )
        
        # Create HistoryTaskItem
        history_item = HistoryTaskItem(
            task_id=task.task_id,
            video_details=task.video_details or VideoDetails(),
            completion_time=task.processing_status.estimated_end_time or "",
            processing_duration=processing_duration,
            audio_output=audio_output,
            summary=summary,
            error_message=task.error_message
        )
        history_items.append(history_item)
    
    # Create and return the TaskHistoryResponse
    return TaskHistoryResponse(
        tasks=history_items,
        total_tasks=total_tasks,
        limit=limit,
        offset=offset
    )

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

# To run the app (example):
# uvicorn src.main:app --reload 