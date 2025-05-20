import pytest
import uuid
from datetime import datetime, timezone
from pydantic import HttpUrl
from unittest.mock import patch

# Assuming src is in pythonpath or tests are run from project root
from src.core import task_manager
from src.models.api_models import (
    TaskStatusResponse, ProcessingStatus, AgentNode, DataFlow, TimelineEvent, 
    VideoDetails, ProcessUrlRequest, AgentLog
)
from src.config.settings import settings # For default agent structure comparison

@pytest.fixture(autouse=True)
def reset_task_store():
    """Clears the in-memory task store before each test."""
    task_manager._tasks_store.clear()
    yield
    task_manager._tasks_store.clear()

@pytest.fixture
def sample_video_url() -> HttpUrl:
    return HttpUrl("http://www.youtube.com/watch?v=dQw4w9WgXcQ")

@pytest.fixture
def sample_process_request(sample_video_url: HttpUrl) -> ProcessUrlRequest:
    return ProcessUrlRequest(youtube_url=sample_video_url)


def test_add_new_task(sample_video_url: HttpUrl, sample_process_request: ProcessUrlRequest):
    """Test creating a new task and its initial state."""
    response_data = task_manager.add_new_task(sample_video_url, sample_process_request)
    
    assert "task_id" in response_data
    task_id = response_data["task_id"]
    assert response_data["status"] == "queued"
    assert response_data["video_details"]["title"] == "Video Title (Fetching...)" # Mocked title

    assert task_id in task_manager._tasks_store
    stored_task_status = task_manager._tasks_store[task_id]
    
    assert isinstance(stored_task_status, TaskStatusResponse)
    assert stored_task_status.task_id == task_id
    assert stored_task_status.processing_status.status == "queued"
    assert stored_task_status.processing_status.overall_progress == 0
    assert stored_task_status.processing_status.start_time is not None
    
    # Check initial agents (count and basic properties)
    # Match the structure defined in task_manager.create_initial_task_status
    expected_agent_ids = [
        "youtube-node", "transcript-fetcher", "summarizer-agent", 
        "synthesizer-agent", "audio-generator", "ui-player"
    ]
    assert len(stored_task_status.agents) == len(expected_agent_ids)
    for i, agent_id in enumerate(expected_agent_ids):
        assert stored_task_status.agents[i].id == agent_id
        assert stored_task_status.agents[i].status == "pending"
        assert stored_task_status.agents[i].progress == 0

    # Check initial data flows (count)
    # Based on the pairs defined in task_manager.create_initial_task_status
    assert len(stored_task_status.data_flows) == len(expected_agent_ids) -1 

    assert len(stored_task_status.timeline) == 1
    assert stored_task_status.timeline[0].event_type == "TASK_CREATED"
    assert str(sample_video_url) in stored_task_status.timeline[0].message

def test_get_task_status_existing(sample_video_url: HttpUrl, sample_process_request: ProcessUrlRequest):
    response_data = task_manager.add_new_task(sample_video_url, sample_process_request)
    task_id = response_data["task_id"]
    
    retrieved_status = task_manager.get_task_status(task_id)
    assert retrieved_status is not None
    assert retrieved_status.task_id == task_id
    assert retrieved_status == task_manager._tasks_store[task_id]

def test_get_task_status_non_existent():
    retrieved_status = task_manager.get_task_status("non-existent-task-id")
    assert retrieved_status is None

def test_update_task_processing_status(sample_video_url: HttpUrl, sample_process_request: ProcessUrlRequest):
    response_data = task_manager.add_new_task(sample_video_url, sample_process_request)
    task_id = response_data["task_id"]
    
    new_overall_status = "processing"
    new_progress = 25.5
    current_agent = "transcript-fetcher"
    
    with patch('src.core.task_manager.datetime') as mock_datetime:
        mock_now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = mock_now
        iso_now = mock_now.isoformat()

        task_manager.update_task_processing_status(task_id, new_overall_status, new_progress, current_agent)

    updated_status = task_manager.get_task_status(task_id)
    assert updated_status.processing_status.status == new_overall_status
    assert updated_status.processing_status.overall_progress == new_progress
    assert updated_status.processing_status.current_agent_id == current_agent
    assert updated_status.timeline[-1].event_type == "PROCESSING_UPDATE"
    assert updated_status.timeline[-1].message == f"Overall status changed to {new_overall_status}"
    assert updated_status.timeline[-1].timestamp == iso_now

def test_update_agent_status(sample_video_url: HttpUrl, sample_process_request: ProcessUrlRequest):
    response_data = task_manager.add_new_task(sample_video_url, sample_process_request)
    task_id = response_data["task_id"]
    agent_to_update = "transcript-fetcher"
    
    new_agent_status = "running"
    new_agent_progress = 50.0
    start_time_iso = datetime.now(timezone.utc).isoformat()

    with patch('src.core.task_manager.datetime') as mock_datetime:
        mock_now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = mock_now
        iso_now_for_timeline = mock_now.isoformat()

        task_manager.update_agent_status(task_id, agent_to_update, new_agent_status, new_agent_progress, start_time=start_time_iso)

    updated_status = task_manager.get_task_status(task_id)
    updated_agent = next((agent for agent in updated_status.agents if agent.id == agent_to_update), None)
    
    assert updated_agent is not None
    assert updated_agent.status == new_agent_status
    assert updated_agent.progress == new_agent_progress
    assert updated_agent.start_time == start_time_iso
    assert updated_agent.end_time is None

    assert updated_status.timeline[-1].event_type == f"AGENT_{new_agent_status.upper()}"
    assert updated_status.timeline[-1].agent_id == agent_to_update
    assert updated_status.timeline[-1].timestamp == iso_now_for_timeline

    # Test agent completion
    end_time_iso = datetime.now(timezone.utc).isoformat()
    task_manager.update_agent_status(task_id, agent_to_update, "completed", 100.0, end_time=end_time_iso)
    updated_status_completed = task_manager.get_task_status(task_id)
    completed_agent = next((agent for agent in updated_status_completed.agents if agent.id == agent_to_update), None)
    assert completed_agent.status == "completed"
    assert completed_agent.progress == 100.0
    assert completed_agent.end_time == end_time_iso

def test_add_agent_log(sample_video_url: HttpUrl, sample_process_request: ProcessUrlRequest):
    response_data = task_manager.add_new_task(sample_video_url, sample_process_request)
    task_id = response_data["task_id"]
    agent_id_to_log = "summarizer-agent"
    log_level = "INFO"
    log_message = "Summarization started with model X."

    with patch('src.core.task_manager.datetime') as mock_datetime:
        mock_now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = mock_now
        iso_now = mock_now.isoformat()

        task_manager.add_agent_log(task_id, agent_id_to_log, log_level, log_message)

    updated_status = task_manager.get_task_status(task_id)
    logged_agent = next((agent for agent in updated_status.agents if agent.id == agent_id_to_log), None)
    
    assert logged_agent is not None
    assert len(logged_agent.logs) == 1
    assert logged_agent.logs[0].level == log_level
    assert logged_agent.logs[0].message == log_message
    assert logged_agent.logs[0].timestamp == iso_now

def test_update_data_flow_status(sample_video_url: HttpUrl, sample_process_request: ProcessUrlRequest):
    response_data = task_manager.add_new_task(sample_video_url, sample_process_request)
    task_id = response_data["task_id"]
    
    # Assuming first data flow is from youtube-source to transcript-fetcher
    from_agent = "youtube-source"
    to_agent = "transcript-fetcher"
    new_flow_status = "transferring"

    with patch('src.core.task_manager.datetime') as mock_datetime:
        mock_now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = mock_now
        iso_now = mock_now.isoformat()
        task_manager.update_data_flow_status(task_id, from_agent, to_agent, new_flow_status)

    updated_status = task_manager.get_task_status(task_id)
    updated_flow = next((flow for flow in updated_status.data_flows if flow.from_agent_id == from_agent and flow.to_agent_id == to_agent), None)
    
    assert updated_flow is not None
    assert updated_flow.status == new_flow_status
    assert updated_status.timeline[-1].event_type == "DATA_FLOW_UPDATE"
    assert updated_status.timeline[-1].timestamp == iso_now

def test_set_task_completed(sample_video_url: HttpUrl, sample_process_request: ProcessUrlRequest):
    response_data = task_manager.add_new_task(sample_video_url, sample_process_request)
    task_id = response_data["task_id"]
    summary_text = "This is the final summary."
    audio_url = "/api/v1/audio/test_audio.mp3"

    with patch('src.core.task_manager.datetime') as mock_datetime:
        mock_now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = mock_now
        iso_now = mock_now.isoformat()
        task_manager.set_task_completed(task_id, summary_text, audio_url)

    completed_task = task_manager.get_task_status(task_id)
    assert completed_task.processing_status.status == "completed"
    assert completed_task.processing_status.overall_progress == 100
    assert completed_task.summary_text == summary_text
    assert completed_task.audio_file_url == audio_url
    assert completed_task.processing_status.estimated_end_time == iso_now # Based on mock
    assert completed_task.timeline[-1].event_type == "TASK_COMPLETED"
    assert completed_task.timeline[-1].timestamp == iso_now

def test_set_task_failed(sample_video_url: HttpUrl, sample_process_request: ProcessUrlRequest):
    response_data = task_manager.add_new_task(sample_video_url, sample_process_request)
    task_id = response_data["task_id"]
    error_msg = "A critical error occurred during transcription."

    # Simulate some progress before failure
    task_manager.update_task_processing_status(task_id, "processing", 30.0)
    initial_progress = task_manager.get_task_status(task_id).processing_status.overall_progress

    with patch('src.core.task_manager.datetime') as mock_datetime:
        mock_now = datetime.now(timezone.utc)
        mock_datetime.now.return_value = mock_now
        iso_now = mock_now.isoformat()
        task_manager.set_task_failed(task_id, error_msg)

    failed_task = task_manager.get_task_status(task_id)
    assert failed_task.processing_status.status == "failed"
    assert failed_task.processing_status.overall_progress == initial_progress # Progress should be preserved
    assert failed_task.error_message == error_msg
    assert failed_task.summary_text is None
    assert failed_task.audio_file_url is None
    assert failed_task.processing_status.estimated_end_time == iso_now # Based on mock
    assert failed_task.timeline[-1].event_type == "TASK_FAILED"
    assert failed_task.timeline[-1].timestamp == iso_now 

def test_task_creation_with_invalid_request():
    """Test that task creation handles invalid requests appropriately."""
    # Create an invalid request (missing required fields)
    invalid_request = ProcessUrlRequest(youtube_url=None)  # type: ignore
    
    with pytest.raises(ValueError, match="youtube_url"):
        task_manager.add_new_task(None, invalid_request)  # type: ignore

def test_task_status_validation():
    """Test that task status updates validate their inputs."""
    sample_url = HttpUrl("http://www.youtube.com/watch?v=dQw4w9WgXcQ")
    request = ProcessUrlRequest(youtube_url=sample_url)
    response = task_manager.add_new_task(sample_url, request)
    task_id = response["task_id"]

    # Test invalid progress value
    with pytest.raises(ValueError, match="progress"):
        task_manager.update_task_processing_status(task_id, "processing", 101.0, "agent-1")
    
    # Test invalid status
    with pytest.raises(ValueError, match="status"):
        task_manager.update_task_processing_status(task_id, "invalid_status", 50.0, "agent-1")
    
    # Test invalid agent ID
    with pytest.raises(ValueError, match="agent"):
        task_manager.update_task_processing_status(task_id, "processing", 50.0, "non-existent-agent")

def test_task_metrics_tracking():
    """Test that task metrics are properly tracked throughout the task lifecycle."""
    sample_url = HttpUrl("http://www.youtube.com/watch?v=dQw4w9WgXcQ")
    request = ProcessUrlRequest(youtube_url=sample_url)
    response = task_manager.add_new_task(sample_url, request)
    task_id = response["task_id"]

    # Mock time for consistent testing
    with patch('src.core.task_manager.datetime') as mock_datetime:
        start_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = start_time
        
        # Update task status and check metrics
        task_manager.update_task_processing_status(task_id, "processing", 25.0, "transcript-fetcher")
        status = task_manager.get_task_status(task_id)
        assert status.processing_status.start_time == start_time.isoformat()
        
        # Move time forward 5 minutes
        progress_time = start_time.replace(minute=5)
        mock_datetime.now.return_value = progress_time
        task_manager.update_task_processing_status(task_id, "processing", 50.0, "summarizer-agent")
        status = task_manager.get_task_status(task_id)
        
        # Elapsed time should be tracked
        assert status.processing_status.elapsed_time == "00:05:00"
        
        # Move time forward another 5 minutes and complete the task
        end_time = start_time.replace(minute=10)
        mock_datetime.now.return_value = end_time
        task_manager.set_task_completed(task_id, "Summary", "/audio/test.mp3")
        status = task_manager.get_task_status(task_id)
        
        # Final metrics should be accurate
        assert status.processing_status.elapsed_time == "00:10:00"
        assert status.processing_status.estimated_end_time == end_time.isoformat()

def test_concurrent_task_updates():
    """Test that task updates handle concurrent modifications safely."""
    sample_url = HttpUrl("http://www.youtube.com/watch?v=dQw4w9WgXcQ")
    request = ProcessUrlRequest(youtube_url=sample_url)
    response = task_manager.add_new_task(sample_url, request)
    task_id = response["task_id"]

    # Simulate concurrent updates to the same task
    import threading
    import time
    
    def update_task(progress: float):
        time.sleep(0.1)  # Simulate some processing time
        task_manager.update_task_processing_status(task_id, "processing", progress, "transcript-fetcher")
    
    # Create threads for concurrent updates
    threads = [
        threading.Thread(target=update_task, args=(25.0,)),
        threading.Thread(target=update_task, args=(50.0,)),
        threading.Thread(target=update_task, args=(75.0,))
    ]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify task state is consistent
    final_status = task_manager.get_task_status(task_id)
    assert final_status is not None
    assert final_status.processing_status.status == "processing"
    assert 0 <= final_status.processing_status.overall_progress <= 100
    
    # Timeline should have recorded all updates in order
    progress_updates = [
        event for event in final_status.timeline 
        if event.event_type == "PROCESSING_UPDATE"
    ]
    assert len(progress_updates) == 3  # All updates should be recorded
    
    # Each update should have a unique timestamp
    timestamps = [update.timestamp for update in progress_updates]
    assert len(set(timestamps)) == len(timestamps)  # All timestamps should be unique

def test_task_cleanup():
    """Test that completed/failed tasks are properly cleaned up."""
    sample_url = HttpUrl("http://www.youtube.com/watch?v=dQw4w9WgXcQ")
    request = ProcessUrlRequest(youtube_url=sample_url)
    
    # Create multiple tasks
    task1 = task_manager.add_new_task(sample_url, request)
    task2 = task_manager.add_new_task(sample_url, request)
    task3 = task_manager.add_new_task(sample_url, request)
    
    # Complete, fail, and leave one pending
    task_manager.set_task_completed(task1["task_id"], "Summary 1", "/audio/test1.mp3")
    task_manager.set_task_failed(task2["task_id"], "Error occurred")
    
    # Verify task states
    assert task_manager.get_task_status(task1["task_id"]).processing_status.status == "completed"
    assert task_manager.get_task_status(task2["task_id"]).processing_status.status == "failed"
    assert task_manager.get_task_status(task3["task_id"]).processing_status.status == "queued"
    
    # If task_manager has a cleanup method, test it here
    if hasattr(task_manager, 'cleanup_old_tasks'):
        with patch('src.core.task_manager.datetime') as mock_datetime:
            # Mock time to be 2 days later
            future_time = datetime.now(timezone.utc).replace(day=datetime.now(timezone.utc).day + 2)
            mock_datetime.now.return_value = future_time
            
            task_manager.cleanup_old_tasks(max_age_hours=24)
            
            # Completed and failed tasks older than 24 hours should be removed
            assert task_manager.get_task_status(task1["task_id"]) is None
            assert task_manager.get_task_status(task2["task_id"]) is None
            # Active task should remain
            assert task_manager.get_task_status(task3["task_id"]) is not None 