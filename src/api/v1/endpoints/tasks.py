from fastapi import APIRouter, HTTPException, BackgroundTasks, Path as FastApiPath, WebSocket, WebSocketDisconnect
import logging

from src.models.api_models import (
    ProcessUrlRequest, ProcessUrlResponse,
    TaskStatusResponse,
    TaskHistoryResponse, HistoryTaskItem, AudioOutput, SummaryContent, VideoDetails
)
from src.core import task_manager
from src.core.connection_manager import manager as ws_manager
from src.processing.pipeline import run_processing_pipeline # Import the pipeline runner
from src.config.settings import settings # Import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process_youtube_url", response_model=ProcessUrlResponse, status_code=202)
async def process_youtube_url_endpoint(
    request: ProcessUrlRequest,
    background_tasks: BackgroundTasks
):
    """
    Accepts a YouTube URL and optional configurations, then triggers the backend processing pipeline.
    Returns a task ID for status polling.
    """
    task_details = task_manager.add_new_task(request.youtube_url, request)

    background_tasks.add_task(run_processing_pipeline, task_details["task_id"], request)
    logger.info(f"Task {task_details['task_id']} added to background processing for URL: {request.youtube_url}")
    
    return ProcessUrlResponse(**task_details)

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status_endpoint(task_id: str = FastApiPath(..., title="The ID of the task to get status for")):
    """
    Returns the detailed status of a processing task.
    """
    status = task_manager.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@router.websocket("/ws/status/{task_id}")
async def websocket_status_endpoint(websocket: WebSocket, task_id: str = FastApiPath(..., title="Task ID to subscribe for status updates")):
    await ws_manager.connect(websocket, task_id)
    logger.info(f"WebSocket client connected for task_id: {task_id}")

    initial_status = task_manager.get_task_status(task_id)
    if initial_status:
        try:
            await websocket.send_json(initial_status.dict())
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, task_id)
            logger.warning(f"WebSocket client for task {task_id} disconnected before initial status send.")
            return
        except Exception as e:
            logger.error(f"Error sending initial status to WebSocket for task {task_id}: {e}")
    else:
        logger.warning(f"Task {task_id} not found when WebSocket connected. Client will wait for updates.")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for task_id: {task_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket connection for task {task_id}: {e}", exc_info=True)
    finally:
        ws_manager.disconnect(websocket, task_id)
        logger.info(f"Cleaned up WebSocket connection for task_id: {task_id}")

@router.get("/history", response_model=TaskHistoryResponse)
async def get_task_history_endpoint(
    limit: int = 10, 
    offset: int = 0
):
    """
    Returns a paginated list of completed tasks with their summaries and audio links.
    """
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be a positive integer")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be a non-negative integer")
    
    max_limit = 100
    if limit > max_limit:
        limit = max_limit
    
    completed_tasks = [
        task for task_id, task in task_manager._tasks_store.items()
        if task.processing_status.status == "completed"
    ]
    
    completed_tasks.sort(
        key=lambda task: task.processing_status.estimated_end_time or "", 
        reverse=True
    )
    
    total_tasks = len(completed_tasks)
    paginated_tasks = completed_tasks[offset:offset+limit]
    
    history_items = []
    for task in paginated_tasks:
        processing_duration = "Unknown"
        if task.processing_status.start_time and task.processing_status.estimated_end_time:
            processing_duration = task.processing_status.elapsed_time or "Unknown"
        
        audio_output = None
        if task.audio_file_url:
            audio_output = AudioOutput(
                url=task.audio_file_url,
                duration="00:03:00",  # Placeholder
                file_size="3.0MB"     # Placeholder
            )
        
        summary = None
        if task.summary_text:
            summary = SummaryContent(
                title=f"Summary: {task.video_details.title if task.video_details else 'Unknown'}",
                host=task.video_details.channel_name if task.video_details else "Unknown",
                main_points=["Point extracted from summary"], # Placeholder
                highlights=["Highlight extracted from summary"], # Placeholder
                key_quotes=["Quote extracted from summary"] # Placeholder
            )
        
        history_item = HistoryTaskItem(
            task_id=task.task_id,
            video_details=task.video_details or VideoDetails(), # Ensure VideoDetails() if None
            completion_time=task.processing_status.estimated_end_time or "",
            processing_duration=processing_duration,
            audio_output=audio_output,
            summary=summary,
            error_message=task.error_message
        )
        history_items.append(history_item)
    
    return TaskHistoryResponse(
        tasks=history_items,
        total_tasks=total_tasks,
        limit=limit,
        offset=offset
    ) 