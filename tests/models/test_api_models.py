import pytest
from pydantic import ValidationError, HttpUrl
from typing import List, Dict, Any, Optional

from src.models.api_models import (
    ConfigOption, ApiConfigResponse,
    ProcessUrlRequest, VideoDetails, ProcessUrlResponse,
    AgentLog, AgentNode, DataFlow, TimelineEvent, ProcessingStatus, TaskStatusResponse,
    HistoryTaskItem, TaskHistoryResponse, MessageResponse, AudioOutput, SummaryContent
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

def test_video_details_with_history_fields():
    data = {
        "title": "Test Video with History",
        "thumbnail": "http://example.com/thumb.jpg",
        "channel_name": "Test Channel History",
        "duration": 300,
        "url": "http://youtube.com/watch?v=video123",
        "upload_date": "2023-07-15"
    }
    model = VideoDetails(**data)
    assert model.title == data["title"]
    assert str(model.thumbnail) == data["thumbnail"]
    assert model.channel_name == data["channel_name"]
    assert model.duration == data["duration"]
    assert str(model.url) == data["url"]
    assert model.upload_date == data["upload_date"]

def test_video_details_history_fields_optional():
    data = {
        "title": "Test Video Minimal History",
    }
    model = VideoDetails(**data)
    assert model.url is None
    assert model.upload_date is None

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

def test_agent_node_defaults():
    # Test that AgentNode initializes with default empty logs and metrics if not provided
    # As per roadmap, logs and metrics should default to None
    node = AgentNode(
        id="agent-123",
        name="Test Agent",
        description="This is a test agent.",
        type="test_type",
        status="pending",
        icon="Cpu" # Lucide icon name
    )
    assert node.logs is None
    assert node.metrics is None
    assert node.progress == 0.0

def test_agent_node_with_values():
    # Test AgentNode with all values provided
    log_entry = AgentLog(timestamp="2023-01-01T12:00:00Z", level="INFO", message="Agent started")
    node = AgentNode(
        id="agent-456",
        name="Processing Agent",
        description="Processes data.",
        type="processing",
        status="running",
        progress=50.0,
        start_time="2023-01-01T12:00:00Z",
        end_time=None,
        icon="Zap",
        logs=[log_entry],
        metrics={"items_processed": 100}
    )
    assert node.id == "agent-456"
    assert node.name == "Processing Agent"
    assert node.description == "Processes data."
    assert node.type == "processing"
    assert node.status == "running"
    assert node.progress == 50.0
    assert node.start_time == "2023-01-01T12:00:00Z"
    assert node.end_time is None
    assert node.icon == "Zap"
    assert node.logs == [log_entry]
    assert node.metrics == {"items_processed": 100}

def test_agent_node_invalid_progress():
    # Test that progress outside the 0-100 range raises a validation error
    with pytest.raises(ValidationError):
        AgentNode(
            id="agent-789",
            name="Error Agent",
            description="Agent with invalid progress.",
            type="error_test",
            status="pending",
            icon="AlertTriangle",
            progress=101.0 
        )
    
    with pytest.raises(ValidationError):
        AgentNode(
            id="agent-789",
            name="Error Agent",
            description="Agent with invalid progress.",
            type="error_test",
            status="pending",
            icon="AlertTriangle",
            progress=-1.0
        )

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

# Test for AudioOutput (New Model)
def test_audio_output_valid():
    data = {
        "url": "/audio/digest-123.mp3",
        "duration": "00:05:30",
        "file_size": "5.2MB"
    }
    model = AudioOutput(**data)
    assert model.url == data["url"]
    assert model.duration == data["duration"]
    assert model.file_size == data["file_size"]

# Test for SummaryContent (New Model)
def test_summary_content_valid():
    data = {
        "title": "Podcast Insights",
        "host": "Dr. Jane Doe",
        "main_points": ["Point 1", "Point 2"],
        "highlights": ["Highlight A", "Highlight B"],
        "key_quotes": ["Quote X", "Quote Y"]
    }
    model = SummaryContent(**data)
    assert model.title == data["title"]
    assert model.host == data["host"]
    assert model.main_points == data["main_points"]
    assert model.highlights == data["highlights"]
    assert model.key_quotes == data["key_quotes"]

def test_summary_content_optional_host():
    data = {
        "title": "Podcast Insights No Host",
        "main_points": ["Point 1"],
        "highlights": ["Highlight A"],
        "key_quotes": ["Quote X"]
    }
    model = SummaryContent(**data)
    assert model.title == data["title"]
    assert model.host is None
    assert model.main_points == data["main_points"]

# Updated Test for HistoryTaskItem
def test_history_task_item_updated_structure():
    video_details_data = {
        "title": "Understanding AI",
        "thumbnail": "http://example.com/ai.jpg",
        "channel_name": "AI Explained",
        "duration": 1200,
        "url": "http://youtube.com/watch?v=ai123",
        "upload_date": "2023-05-01"
    }
    audio_output_data = {
        "url": "/audio/ai-digest.mp3",
        "duration": "00:03:15",
        "file_size": "3.1MB"
    }
    summary_content_data = {
        "title": "AI Key Takeaways",
        "host": "AI Bot",
        "main_points": ["AI is evolving fast."],
        "highlights": ["Neural networks are key."],
        "key_quotes": ["The future is AI."]
    }
    data = {
        "task_id": "hist-task-updated-1",
        "video_details": video_details_data,
        "completion_time": "2023-05-01T14:30:00Z",
        "processing_duration": "00:10:00",
        "audio_output": audio_output_data,
        "summary": summary_content_data,
        "error_message": None
    }
    model = HistoryTaskItem(**data)
    assert model.task_id == data["task_id"]
    assert model.video_details.title == video_details_data["title"]
    assert str(model.video_details.url) == video_details_data["url"]
    assert model.completion_time == data["completion_time"]
    assert model.processing_duration == data["processing_duration"]
    assert model.audio_output.url == audio_output_data["url"]
    assert model.summary.title == summary_content_data["title"]
    assert model.error_message is None

def test_history_task_item_with_error():
    video_details_data = {"title": "Failed Task Video"} # Minimal for brevity
    data = {
        "task_id": "hist-task-error-1",
        "video_details": video_details_data,
        "completion_time": "2023-05-02T10:00:00Z",
        "processing_duration": "00:01:00",
        "audio_output": None, # No audio output if failed
        "summary": None,      # No summary if failed
        "error_message": "Failed due to API timeout"
    }
    model = HistoryTaskItem(**data)
    assert model.error_message == data["error_message"]
    assert model.audio_output is None
    assert model.summary is None

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