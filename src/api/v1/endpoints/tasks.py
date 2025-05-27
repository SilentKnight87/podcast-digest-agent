import asyncio
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi import Path as FastApiPath

# from src.runners.simple_pipeline import SimplePipeline  # Deprecated - using ADK only
from src.adk_runners.pipeline_runner import AdkPipelineRunner  # Import ADK pipeline

# Import agents
from src.config.settings import settings  # Import settings
from src.core import task_manager
from src.core.connection_manager import manager as ws_manager
from src.models.api_models import (
    AudioOutput,
    HistoryTaskItem,
    ProcessUrlRequest,
    ProcessUrlResponse,
    SummaryContent,
    TaskHistoryResponse,
    TaskStatusResponse,
    VideoDetails,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# Deprecated function - keeping for reference only
# async def run_real_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
#     """Run the actual processing pipeline using the SimplePipeline."""
#     pass


async def run_adk_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """Run the ADK-based processing pipeline with WebSocket support."""
    logger.info(f"Starting ADK pipeline for task {task_id}")

    try:
        # Extract video ID
        youtube_url = str(request_data.youtube_url)
        logger.info(f"Processing YouTube URL: {youtube_url}")

        video_id = extract_video_id_from_url(youtube_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")

        logger.info(f"Extracted video ID: {video_id}")

        # Update task status
        task_manager.update_task_processing_status(
            task_id, "processing", progress=5, current_agent_id="transcript-fetcher"
        )
        logger.info(f"Task {task_id} status updated to processing")

        # Run ADK pipeline with task_id for WebSocket updates
        logger.info("Creating ADK pipeline runner...")
        adk_pipeline = AdkPipelineRunner()

        logger.info(f"Starting ADK pipeline execution for video ID: {video_id}")
        result = await adk_pipeline.run_async(
            video_ids=[video_id],
            output_dir=settings.OUTPUT_AUDIO_DIR,
            task_id=task_id,  # Pass task_id for WebSocket bridge
        )

        # Process results - the pipeline runner handles task completion internally
        if result.get("success"):
            logger.info(f"ADK pipeline completed successfully for task {task_id}")
            logger.info(f"Final audio path: {result.get('final_audio_path')}")
        else:
            error_message = result.get("error", "Unknown ADK pipeline error")
            logger.error(f"ADK pipeline failed for task {task_id}: {error_message}")
            # Only set failed if the pipeline didn't already handle it
            task_manager.set_task_failed(task_id, error_message)

    except Exception as e:
        logger.error(f"Error in ADK pipeline for task {task_id}: {e}", exc_info=True)
        task_manager.set_task_failed(task_id, str(e))


def extract_video_id_from_url(youtube_url: str) -> str:
    """Extract video ID from YouTube URL."""
    import re

    # Match various YouTube URL formats
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)",
        r"youtube\.com/watch\?.*v=([^&\n?#]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)

    return None


@router.post("/process_youtube_url", response_model=ProcessUrlResponse, status_code=202)
async def process_youtube_url_endpoint(request: ProcessUrlRequest):
    """
    Accepts a YouTube URL and optional configurations, then triggers the backend processing pipeline.
    Returns a task ID for status polling.
    """
    task_details = task_manager.add_new_task(request.youtube_url, request)

    # Always use ADK pipeline - use asyncio.create_task for proper async handling
    asyncio.create_task(run_adk_processing_pipeline(task_details["task_id"], request))
    logger.info(
        f"Task {task_details['task_id']} added to ADK background processing for URL: {request.youtube_url}"
    )

    return ProcessUrlResponse(**task_details)


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status_endpoint(
    task_id: str = FastApiPath(..., title="The ID of the task to get status for")
):
    """
    Returns the detailed status of a processing task.
    """
    status = task_manager.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@router.websocket("/ws/status/{task_id}")
async def websocket_status_endpoint(
    websocket: WebSocket,
    task_id: str = FastApiPath(..., title="Task ID to subscribe for status updates"),
):
    await ws_manager.connect(websocket, task_id)
    logger.info(f"WebSocket client connected for task_id: {task_id}")

    initial_status = task_manager.get_task_status(task_id)
    if initial_status:
        try:
            await websocket.send_json(initial_status.model_dump())
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket, task_id)
            logger.warning(
                f"WebSocket client for task {task_id} disconnected before initial status send."
            )
            return
        except Exception as e:
            logger.error(f"Error sending initial status to WebSocket for task {task_id}: {e}")
    else:
        logger.warning(
            f"Task {task_id} not found when WebSocket connected. Client will wait for updates."
        )

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
async def get_task_history_endpoint(limit: int = 10, offset: int = 0):
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
        task
        for task_id, task in task_manager._tasks_store.items()
        if task.processing_status.status == "completed"
    ]

    completed_tasks.sort(
        key=lambda task: task.processing_status.estimated_end_time or "", reverse=True
    )

    total_tasks = len(completed_tasks)
    paginated_tasks = completed_tasks[offset : offset + limit]

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
                file_size="3.0MB",  # Placeholder
            )

        summary = None
        if task.summary_text:
            # Extract title from summary text if available
            title = "Podcast Digest Summary"
            if task.summary_text.startswith("ADK Generated Summary:"):
                title = task.summary_text.split(":")[0]

            summary = SummaryContent(
                title=title,
                host="AI Podcast Digest",  # Default host
                main_points=["Point extracted from summary"],  # Placeholder
                highlights=["Highlight extracted from summary"],  # Placeholder
                key_quotes=["Quote extracted from summary"],  # Placeholder
            )

        # Create default video details since it's not stored in TaskStatusResponse
        video_details = VideoDetails(
            title="YouTube Video", channel_name="Unknown Channel", url=None
        )

        history_item = HistoryTaskItem(
            task_id=task.task_id,
            video_details=video_details,
            completion_time=task.processing_status.estimated_end_time or "",
            processing_duration=processing_duration,
            audio_output=audio_output,
            summary=summary,
            error_message=task.error_message,
        )
        history_items.append(history_item)

    return TaskHistoryResponse(
        tasks=history_items, total_tasks=total_tasks, limit=limit, offset=offset
    )
