import pytest
from pydantic import ValidationError, HttpUrl

from src.models.api_models import (
    ConfigOption, ApiConfigResponse,
    ProcessUrlRequest, VideoDetails, ProcessUrlResponse,
    AgentLog, AgentNode, DataFlow, TimelineEvent, ProcessingStatus, TaskStatusResponse,
    HistoryTaskItem, TaskHistoryResponse, MessageResponse
)

def test_config_option_valid():
    data = {"name": "Voice A", "value": "en-US-VoiceA"}
    model = ConfigOption(**data)
    assert model.name == data["name"]
    assert model.value == data["value"]

def test_api_config_response_valid():
    data = {
        "available_tts_voices": [{"name": "Voice A", "value": "en-US-VoiceA"}],
        "available_summary_lengths": [{"name": "Short", "value": "short"}],
        "available_audio_styles": [{"name": "Neutral", "value": "neutral"}]
    }
    model = ApiConfigResponse(**data)
    assert len(model.available_tts_voices) == 1
    assert model.available_tts_voices[0].name == "Voice A"

# --- /process_youtube_url Endpoint --- 
def test_process_url_request_valid():
    data = {"youtube_url": "http://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    model = ProcessUrlRequest(**data)
    assert str(model.youtube_url) == data["youtube_url"]
    assert model.summary_length is None

def test_process_url_request_invalid_url():
    with pytest.raises(ValidationError):
        ProcessUrlRequest(youtube_url="not_a_url")

def test_process_url_request_optional_fields():
    data = {
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "summary_length": "long",
        "tts_voice": "en-GB-Neural2-A",
        "audio_style": "upbeat"
    }
    model = ProcessUrlRequest(**data)
    assert model.summary_length == "long"
    assert model.tts_voice == "en-GB-Neural2-A"
    assert model.audio_style == "upbeat"

def test_video_details_valid():
    data = {
        "title": "Test Video",
        "thumbnail": "http://example.com/thumb.jpg",
        "channel_name": "Test Channel",
        "duration": 300
    }
    model = VideoDetails(**data)
    assert model.title == data["title"]
    assert str(model.thumbnail) == data["thumbnail"]
    assert model.duration == 300

def test_video_details_defaults():
    model = VideoDetails()
    assert model.title == "Unknown Title"
    assert model.thumbnail is None
    assert model.channel_name == "Unknown Channel"
    assert model.duration is None

def test_process_url_response_valid():
    video_data = {"title": "Processed Video"}
    data = {
        "task_id": "task-123",
        "status": "queued",
        "video_details": video_data
    }
    model = ProcessUrlResponse(**data)
    assert model.task_id == "task-123"
    assert model.status == "queued"
    assert model.video_details.title == "Processed Video"

# --- /status/{task_id} Endpoint --- 
def test_agent_log_valid():
    data = {"timestamp": "2023-01-01T12:00:00Z", "level": "INFO", "message": "Agent started"}
    model = AgentLog(**data)
    assert model.message == "Agent started"

def test_agent_node_valid():
    data = {
        "id": "agent-1", "name": "Transcript Agent", "description": "Transcribes audio",
        "type": "transcription", "status": "running", "progress": 50.5,
        "icon": "FileText",
        "logs": [{"timestamp": "2023-01-01T12:00:00Z", "level": "INFO", "message": "Agent started"}]
    }
    model = AgentNode(**data)
    assert model.id == "agent-1"
    assert model.progress == 50.5
    assert len(model.logs) == 1

def test_agent_node_invalid_progress():
    data = {
        "id": "agent-1", "name": "Test Agent", "description": "Test desc",
        "type": "test", "status": "pending", "icon": "Tool"
    }
    with pytest.raises(ValidationError):
        AgentNode(**data, progress=-10) # Progress < 0
    with pytest.raises(ValidationError):
        AgentNode(**data, progress=110) # Progress > 100

def test_data_flow_valid():
    data = {
        "id": "flow-1", "from_agent_id": "agent-1", "to_agent_id": "agent-2",
        "data_type": "transcript", "status": "transferring"
    }
    model = DataFlow(**data)
    assert model.data_type == "transcript"

def test_timeline_event_valid():
    data = {"timestamp": "2023-01-01T12:05:00Z", "event_type": "AGENT_COMPLETED", "message": "Agent 1 done"}
    model = TimelineEvent(**data)
    assert model.event_type == "AGENT_COMPLETED"

def test_processing_status_valid():
    data = {"overall_progress": 75.0, "status": "processing", "current_agent_id": "agent-2"}
    model = ProcessingStatus(**data)
    assert model.status == "processing"

def test_task_status_response_valid():
    # A more comprehensive test would involve building up all nested models
    data = {
        "task_id": "task-xyz",
        "processing_status": {"overall_progress": 100, "status": "completed"},
        "agents": [], "data_flows": [], "timeline": [],
        "summary_text": "This is a summary.",
        "audio_file_url": "http://example.com/audio.mp3"
    }
    model = TaskStatusResponse(**data)
    assert model.task_id == "task-xyz"
    assert model.processing_status.status == "completed"
    assert model.summary_text == "This is a summary."

# --- /history Endpoint --- 
def test_history_task_item_valid():
    data = {
        "task_id": "hist-task-1",
        "youtube_url": "http://youtube.com/video1",
        "video_title": "History Video 1",
        "status": "completed",
        "created_at": "2023-01-01T10:00:00Z"
    }
    model = HistoryTaskItem(**data)
    assert model.video_title == "History Video 1"

def test_task_history_response_valid():
    item_data = {
        "task_id": "hist-task-1", "youtube_url": "http://youtube.com/video1",
        "video_title": "History Video 1", "status": "completed", "created_at": "2023-01-01T10:00:00Z"
    }
    data = {"tasks": [item_data], "total_tasks": 1, "limit": 10, "offset": 0}
    model = TaskHistoryResponse(**data)
    assert len(model.tasks) == 1
    assert model.tasks[0].task_id == "hist-task-1"
    assert model.total_tasks == 1

# --- General --- 
def test_message_response_valid():
    data = {"message": "Operation successful"}
    model = MessageResponse(**data)
    assert model.message == "Operation successful" 