import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any 
from pydantic import HttpUrl
import asyncio # Import asyncio for create_task

from src.models.api_models import (
    TaskStatusResponse, ProcessingStatus, AgentNode, DataFlow, TimelineEvent, 
    VideoDetails, ProcessUrlRequest, AgentLog
)
from src.config.settings import settings
from src.core.connection_manager import manager as ws_manager # Import WebSocket manager
import logging

logger = logging.getLogger(__name__)

# In-memory store for tasks. 
# In a production scenario, this would be a database (e.g., Redis, PostgreSQL).
_tasks_store: Dict[str, TaskStatusResponse] = {}

async def _broadcast_task_update(task_id: str):
    """Helper function to fetch task status and broadcast it."""
    task_status = get_task_status(task_id)
    if task_status:
        try:
            # ws_manager.broadcast_to_task is async, ensure it's awaited
            # If called from a sync function, it needs to be scheduled.
            # For simplicity, assuming task_manager functions might become async or use a helper.
            await ws_manager.broadcast_to_task(task_id, task_status.dict())
            logger.debug(f"Broadcasted update for task_id: {task_id}")
        except Exception as e:
            logger.error(f"Error broadcasting task update for {task_id}: {e}", exc_info=True)
    else:
        logger.warning(f"Task {task_id} not found for broadcasting update.")

# Wrapper to run async broadcast from sync functions if needed (can be improved with a proper event loop handling)
# For now, let's make the main update functions async directly if they call other async code.
# Alternatively, if these must remain sync, they'd need to schedule _broadcast_task_update 
# using asyncio.create_task() if an event loop is running, or handle it via a queue.

def schedule_broadcast(task_id: str):
    """Schedules the broadcast if an event loop is running."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_broadcast_task_update(task_id))
    except RuntimeError: # No running event loop
        # This case needs careful handling. If FastAPI runs these in threads, 
        # a new loop might be needed or a thread-safe way to signal the main loop.
        # For now, just log. This will be an issue if called from non-async bg tasks.
        logger.warning(f"No running asyncio loop to schedule broadcast for task {task_id}. Update won't be pushed via WebSocket immediately from this context.")

def create_initial_task_status(task_id: str, video_url: HttpUrl, request_data: ProcessUrlRequest) -> TaskStatusResponse:
    """Creates the initial state for a new task."""
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    
    # Define the initial agent pipeline structure based on your processing workflow
    # These should match the agents you intend to run.
    initial_agents = [
        AgentNode(
            id="youtube-node", name="YouTube Video", description="Initial YouTube video source.", 
            type="input_source", status="pending", icon="Youtube", progress=0
        ),
        AgentNode(
            id="transcript-fetcher", name="Transcript Fetcher", description="Fetches video transcript.", 
            type="transcription", status="pending", icon="FileText", progress=0
        ),
        AgentNode(
            id="summarizer-agent", name="Summarizer", description="Generates a summary from the transcript.", 
            type="summarization", status="pending", icon="Brain", progress=0
        ),
        AgentNode(
            id="synthesizer-agent", name="Dialogue Synthesizer", description="Converts summary to dialogue script.", 
            type="synthesis", status="pending", icon="MessageSquare", progress=0
        ),
        AgentNode(
            id="audio-generator", name="Audio Generator", description="Generates audio from the dialogue script.", 
            type="tts", status="pending", icon="Mic", progress=0
        ),
        AgentNode(
            id="ui-player", name="UI/Player", description="Final output for the user.", 
            type="output_display", status="pending", icon="PlayCircle", progress=0
        )
    ]
    
    # Define initial data flows (simplified for now)
    initial_data_flows = [
        DataFlow(id=str(uuid.uuid4()), from_agent_id="youtube-node", to_agent_id="transcript-fetcher", data_type="video_url", status="pending"),
        DataFlow(id=str(uuid.uuid4()), from_agent_id="transcript-fetcher", to_agent_id="summarizer-agent", data_type="transcript", status="pending"),
        DataFlow(id=str(uuid.uuid4()), from_agent_id="summarizer-agent", to_agent_id="synthesizer-agent", data_type="summary", status="pending"),
        DataFlow(id=str(uuid.uuid4()), from_agent_id="synthesizer-agent", to_agent_id="audio-generator", data_type="dialogue_script", status="pending"),
        DataFlow(id=str(uuid.uuid4()), from_agent_id="audio-generator", to_agent_id="ui-player", data_type="audio_file", status="pending"),
    ]

    task_status = TaskStatusResponse(
        task_id=task_id,
        processing_status=ProcessingStatus(
            status="queued",
            start_time=now_utc_iso,
            overall_progress=0
        ),
        agents=initial_agents,
        data_flows=initial_data_flows,
        timeline=[
            TimelineEvent(
                timestamp=now_utc_iso,
                event_type="TASK_CREATED",
                message=f"Task created for URL: {video_url}"
            )
        ]
    )
    return task_status

def add_new_task(video_url: HttpUrl, request_data: ProcessUrlRequest) -> Dict[str, Any]:
    """Creates a new task, stores its initial status, and returns task ID and details."""
    task_id = str(uuid.uuid4())
    
    # Simulate fetching video details (replace with actual fetching logic later)
    # For now, we use some defaults and passed-in data.
    video_details = VideoDetails(
        title="Video Title (Fetching...)", # Placeholder
        # thumbnail= # This would be fetched
        channel_name="Channel Name (Fetching...)", # Placeholder
        # duration= # This would be fetched
    )

    initial_status = create_initial_task_status(task_id, video_url, request_data)
    _tasks_store[task_id] = initial_status
    
    # Schedule broadcast for the newly created task (queued state)
    schedule_broadcast(task_id)
    
    # Create response for the /process_youtube_url endpoint
    # The video_details here are just initial placeholders or quickly fetched info.
    # The full, detailed status is available via the /status/{task_id} endpoint.
    process_response = {
        "task_id": task_id,
        "status": initial_status.processing_status.status,
        "video_details": video_details.dict() # Convert Pydantic model to dict for response
    }
    return process_response

def get_task_status(task_id: str) -> Optional[TaskStatusResponse]:
    """Retrieves the status of a specific task."""
    return _tasks_store.get(task_id)

def update_task_processing_status(task_id: str, new_status: str, progress: Optional[float] = None, current_agent_id: Optional[str] = None):
    task = _tasks_store.get(task_id)
    if task:
        task.processing_status.status = new_status
        if progress is not None:
            task.processing_status.overall_progress = progress
        if current_agent_id:
            task.processing_status.current_agent_id = current_agent_id
        # Add timeline event for status update
        add_timeline_event(task_id, "PROCESSING_UPDATE", f"Overall status changed to {new_status}")
        schedule_broadcast(task_id) # Broadcast after update

def update_agent_status(task_id: str, agent_id: str, new_status: str, progress: Optional[float] = None, start_time: Optional[str] = None, end_time: Optional[str] = None):
    task = _tasks_store.get(task_id)
    if task:
        for agent in task.agents:
            if agent.id == agent_id:
                agent.status = new_status
                if progress is not None:
                    agent.progress = progress
                if start_time:
                    agent.start_time = start_time
                if end_time:
                    agent.end_time = end_time
                add_timeline_event(task_id, f"AGENT_{new_status.upper()}", f"Agent {agent.name} status: {new_status}", agent_id=agent_id)
                break
        schedule_broadcast(task_id) # Broadcast after update

def add_agent_log(task_id: str, agent_id: str, level: str, message: str):
    task = _tasks_store.get(task_id)
    if task:
        for agent in task.agents:
            if agent.id == agent_id:
                if agent.logs is None:
                    agent.logs = []
                agent.logs.append(AgentLog(timestamp=datetime.now(timezone.utc).isoformat(), level=level, message=message))
                break
        schedule_broadcast(task_id) # Broadcast after update

def update_data_flow_status(task_id: str, from_agent_id: str, to_agent_id: str, new_status: str):
    task = _tasks_store.get(task_id)
    if task:
        for flow in task.data_flows:
            if flow.from_agent_id == from_agent_id and flow.to_agent_id == to_agent_id:
                flow.status = new_status
                add_timeline_event(task_id, "DATA_FLOW_UPDATE", f"Data flow {from_agent_id} -> {to_agent_id} status: {new_status}")
                break
        schedule_broadcast(task_id) # Broadcast after update

def add_timeline_event(task_id: str, event_type: str, message: str, agent_id: Optional[str] = None):
    task = _tasks_store.get(task_id)
    if task:
        task.timeline.append(
            TimelineEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type=event_type,
                message=message,
                agent_id=agent_id
            )
        )
        # Note: add_timeline_event itself might not always require an immediate broadcast 
        # if it's usually called along with another status update that triggers broadcast.
        # However, if it can be called standalone and represents a significant update, broadcasting here is fine.
        schedule_broadcast(task_id)

def set_task_completed(task_id: str, summary: str, audio_url: str):
    task = _tasks_store.get(task_id)
    if task:
        task.processing_status.status = "completed"
        task.processing_status.overall_progress = 100
        task.processing_status.estimated_end_time = datetime.now(timezone.utc).isoformat() # Rough estimate
        task.summary_text = summary
        task.audio_file_url = audio_url
        add_timeline_event(task_id, "TASK_COMPLETED", "Task completed successfully.")
        schedule_broadcast(task_id) # Broadcast after update

def set_task_failed(task_id: str, error_message: str):
    task = _tasks_store.get(task_id)
    if task:
        task.processing_status.status = "failed"
        task.processing_status.overall_progress = task.processing_status.overall_progress # Keep current progress or set to specific value
        task.error_message = error_message
        task.processing_status.estimated_end_time = datetime.now(timezone.utc).isoformat() # Rough estimate
        add_timeline_event(task_id, "TASK_FAILED", f"Task failed: {error_message}")
        schedule_broadcast(task_id) # Broadcast after update

# TODO: Add function for listing completed tasks for history (with pagination) 