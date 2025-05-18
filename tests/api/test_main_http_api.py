import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY
import os
from pathlib import Path

# Assuming src is in pythonpath or tests are run from project root
from src.main import app  # The FastAPI application instance
from src.config.settings import settings # To access actual settings for comparison
from src.models.api_models import ApiConfigResponse, ProcessUrlResponse, TaskStatusResponse
from src.core import task_manager # To inspect task store or pre-populate

@pytest.fixture
def client():
    """Provides a TestClient instance for making API requests."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def reset_task_store_for_api_tests():
    """Clears the in-memory task store before each API test function."""
    task_manager._tasks_store.clear()
    yield
    task_manager._tasks_store.clear()

# --- Tests for /api/v1/config --- 
def test_get_config(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/config")
    assert response.status_code == 200
    data = response.json()
    
    # Validate structure using Pydantic model
    parsed_response = ApiConfigResponse(**data)
    assert len(parsed_response.available_tts_voices) == len(settings.AVAILABLE_TTS_VOICES)
    assert parsed_response.available_tts_voices[0].name == settings.AVAILABLE_TTS_VOICES[0]["name"]
    assert parsed_response.available_tts_voices[0].id == settings.AVAILABLE_TTS_VOICES[0]["id"]
    # Similar checks for summary_lengths and audio_styles
    assert len(parsed_response.available_summary_lengths) == len(settings.AVAILABLE_SUMMARY_LENGTHS)
    assert len(parsed_response.available_audio_styles) == len(settings.AVAILABLE_AUDIO_STYLES)

# --- Tests for /api/v1/process_youtube_url --- 
def test_process_youtube_url_valid(client: TestClient):
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    payload = {"youtube_url": youtube_url}
    
    # We can mock the background task if it were being called directly here
    # For now, add_new_task is synchronous in creating the task entry
    with patch('src.main.BackgroundTasks.add_task') as mock_add_task: # Assuming it might be added later
        response = client.post(f"{settings.API_V1_STR}/process_youtube_url", json=payload)
    
    assert response.status_code == 202 # Accepted
    data = response.json()
    parsed_response = ProcessUrlResponse(**data)
    
    assert parsed_response.task_id is not None
    assert parsed_response.status == "queued"
    assert parsed_response.video_details.title == "Video Title (Fetching...)" # Current mock response
    
    # Check if task was actually added to the store
    assert parsed_response.task_id in task_manager._tasks_store
    # mock_add_task.assert_called_once() # Enable if background task is active

def test_process_youtube_url_invalid_url(client: TestClient):
    payload = {"youtube_url": "not-a-valid-url"}
    response = client.post(f"{settings.API_V1_STR}/process_youtube_url", json=payload)
    assert response.status_code == 422 # Unprocessable Entity for Pydantic validation error
    data = response.json()
    assert "detail" in data
    assert data["detail"][0]["type"] == "url_parsing"

# --- Tests for /api/v1/status/{task_id} --- 
def test_get_status_existing_task(client: TestClient):
    # First, create a task directly via task_manager or by calling the process_url endpoint
    from pydantic import HttpUrl
    from src.models.api_models import ProcessUrlRequest
    video_url = HttpUrl("https://www.youtube.com/watch?v=example")
    request_data = ProcessUrlRequest(youtube_url=video_url)
    created_task_details = task_manager.add_new_task(video_url, request_data)
    task_id = created_task_details["task_id"]
    
    response = client.get(f"{settings.API_V1_STR}/status/{task_id}")
    assert response.status_code == 200
    data = response.json()
    parsed_response = TaskStatusResponse(**data)
    assert parsed_response.task_id == task_id
    assert parsed_response.processing_status.status == "queued" # Initial status
    assert len(parsed_response.agents) > 0 # Check some basic structure

def test_get_status_non_existent_task(client: TestClient):
    task_id = "non-existent-task-id-123"
    response = client.get(f"{settings.API_V1_STR}/status/{task_id}")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Task not found"

# --- Tests for /api/v1/audio/{filename} --- 
@pytest.fixture
def setup_mock_audio_file(tmp_path_factory):
    audio_dir_name = settings.OUTPUT_AUDIO_DIR
    # Create a temporary directory that mirrors the structure used by settings
    # If settings.OUTPUT_AUDIO_DIR is absolute, this needs adjustment.
    # Assuming it's relative to project root or a known base for testing.
    
    # For this test, we'll mock settings.OUTPUT_AUDIO_DIR to be a temp path
    # or ensure the test client uses a base_directory that aligns.
    # The easiest is to ensure the file is created where the app expects it.
    
    # Let's assume settings.OUTPUT_AUDIO_DIR is 'output_audio' relative to project root.
    # For testing, we might want to override this path or ensure our TestClient is rooted correctly.
    # The FileResponse in main.py uses Path(settings.OUTPUT_AUDIO_DIR) / filename.
    
    # Create a temporary directory for output_audio for this test
    temp_output_dir = tmp_path_factory.mktemp(Path(settings.OUTPUT_AUDIO_DIR).name) 
    mock_filename = "test_audio_sample.mp3"
    mock_file_path = temp_output_dir / mock_filename
    with open(mock_file_path, "w") as f:
        f.write("dummy audio content")
    
    # Patch settings.OUTPUT_AUDIO_DIR to use this temporary directory for the test duration
    with patch.object(settings, 'OUTPUT_AUDIO_DIR', str(temp_output_dir)):
        yield mock_filename, mock_file_path
    
    # Clean up: pytest tmp_path_factory handles temp dir removal

def test_get_audio_file_exists(client: TestClient, setup_mock_audio_file):
    mock_filename, mock_file_path = setup_mock_audio_file
    
    response = client.get(f"{settings.API_V1_STR}/audio/{mock_filename}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"dummy audio content"

def test_get_audio_file_not_found(client: TestClient):
    response = client.get(f"{settings.API_V1_STR}/audio/non_existent_audio.mp3")
    assert response.status_code == 404
    assert response.json()["detail"] == "Audio file not found."

def test_get_audio_file_path_traversal(client: TestClient):
    # Attempt path traversal - this should be blocked by sanitization in the endpoint
    response = client.get(f"{settings.API_V1_STR}/audio/../../../../etc/passwd")
    # Expecting 400 (Invalid filename) or 403/404 due to path resolution failure / security checks
    assert response.status_code in [400, 403, 404] 
    if response.status_code == 400:
        assert response.json()["detail"] == "Invalid filename."
    # If it resolves but is forbidden, might be 403, or 404 if strict resolve fails higher up.

# Placeholder for /api/v1/history tests (once implemented)
# def test_get_history_empty(client: TestClient):
#     pass

# def test_get_history_with_data(client: TestClient):
#     # Pre-populate task_manager with some completed tasks
#     pass 