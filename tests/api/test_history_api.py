import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.config.settings import settings
from src.core import task_manager
from src.main import app
from src.models.api_models import (
    ProcessingStatus,
    TaskHistoryResponse,
    TaskStatusResponse,
    VideoDetails,
)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_task_store():
    """Clears the task store before and after each test."""
    task_manager._tasks_store.clear()
    yield
    task_manager._tasks_store.clear()


def test_get_history_empty(client: TestClient):
    """Test that the history endpoint returns an empty list when no tasks exist."""
    response = client.get(f"{settings.API_V1_STR}/history")
    assert response.status_code == 200
    data = response.json()

    # Validate structure using Pydantic model
    parsed_response = TaskHistoryResponse(**data)
    assert len(parsed_response.tasks) == 0
    assert parsed_response.total_tasks == 0
    assert parsed_response.limit == 10  # Assuming default limit is 10
    assert parsed_response.offset == 0


def create_mock_completed_task(task_id, title="Test Video", hours_ago=0):
    """Helper to create a mock completed task for testing."""
    now = datetime.now(UTC)
    start_time = (now - timedelta(hours=hours_ago + 1)).isoformat()
    end_time = (now - timedelta(hours=hours_ago)).isoformat()

    # Create video details
    video_details = VideoDetails(
        title=f"{title} {task_id[-4:]}",
        thumbnail="https://example.com/thumb.jpg",
        channel_name="Test Channel",
        duration=1200,  # 20 minutes
        url=f"https://youtube.com/watch?v={task_id}",
        upload_date="2023-06-10",
    )

    # Create a completed task
    task = TaskStatusResponse(
        task_id=task_id,
        processing_status=ProcessingStatus(
            status="completed",
            overall_progress=100,
            start_time=start_time,
            estimated_end_time=end_time,
            elapsed_time="01:00:00",
            remaining_time="00:00:00",
        ),
        agents=[],  # Not needed for history
        data_flows=[],  # Not needed for history
        timeline=[],  # Not needed for history
        summary_text="This is a test summary for the video.",
        audio_file_url=f"/audio/{task_id}.mp3",
    )

    task_manager._tasks_store[task_id] = task
    return task


@pytest.mark.skip("History endpoint not fully implemented yet")
def test_get_history_with_completed_tasks(client: TestClient):
    """Test that the history endpoint returns completed tasks."""
    # Create several completed tasks
    task_id1 = str(uuid.uuid4())
    task_id2 = str(uuid.uuid4())
    task_id3 = str(uuid.uuid4())

    create_mock_completed_task(task_id1, "Video One", hours_ago=2)
    create_mock_completed_task(task_id2, "Video Two", hours_ago=1)
    create_mock_completed_task(task_id3, "Video Three", hours_ago=0)

    # Add a task that is still processing (should not be in history)
    in_progress_task_id = str(uuid.uuid4())
    task_manager._tasks_store[in_progress_task_id] = TaskStatusResponse(
        task_id=in_progress_task_id,
        processing_status=ProcessingStatus(
            status="processing", overall_progress=50, start_time=datetime.now(UTC).isoformat()
        ),
        agents=[],
        data_flows=[],
        timeline=[],
    )

    # Get the history
    response = client.get(f"{settings.API_V1_STR}/history")
    assert response.status_code == 200
    data = response.json()

    # Validate structure
    parsed_response = TaskHistoryResponse(**data)
    assert len(parsed_response.tasks) == 3
    assert parsed_response.total_tasks == 3

    # Check that tasks are ordered by completion time (newest first)
    assert parsed_response.tasks[0].task_id == task_id3
    assert parsed_response.tasks[1].task_id == task_id2
    assert parsed_response.tasks[2].task_id == task_id1

    # Validate first task details
    first_task = parsed_response.tasks[0]
    assert first_task.video_details.title == f"Video Three {task_id3[-4:]}"
    assert first_task.video_details.channel_name == "Test Channel"
    assert first_task.audio_output.url == f"/audio/{task_id3}.mp3"

    # Ensure the in-progress task is not included
    task_ids = [task.task_id for task in parsed_response.tasks]
    assert in_progress_task_id not in task_ids


@pytest.mark.skip("History endpoint not fully implemented yet")
def test_get_history_with_pagination(client: TestClient):
    """Test that the history endpoint supports pagination."""
    # Create 15 completed tasks
    task_ids = []
    for i in range(15):
        task_id = str(uuid.uuid4())
        task_ids.append(task_id)
        create_mock_completed_task(task_id, f"Video {i+1}", hours_ago=i)

    # Test with limit=5, offset=0 (first page)
    response = client.get(f"{settings.API_V1_STR}/history?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    parsed_response = TaskHistoryResponse(**data)

    assert len(parsed_response.tasks) == 5
    assert parsed_response.total_tasks == 15
    assert parsed_response.limit == 5
    assert parsed_response.offset == 0

    # Check that we got the 5 most recent tasks
    for i in range(5):
        assert parsed_response.tasks[i].task_id == task_ids[i]

    # Test with limit=5, offset=5 (second page)
    response = client.get(f"{settings.API_V1_STR}/history?limit=5&offset=5")
    assert response.status_code == 200
    data = response.json()
    parsed_response = TaskHistoryResponse(**data)

    assert len(parsed_response.tasks) == 5
    assert parsed_response.total_tasks == 15
    assert parsed_response.limit == 5
    assert parsed_response.offset == 5

    # Check that we got the next 5 tasks
    for i in range(5):
        assert parsed_response.tasks[i].task_id == task_ids[i + 5]

    # Test with limit=5, offset=10 (third page)
    response = client.get(f"{settings.API_V1_STR}/history?limit=5&offset=10")
    assert response.status_code == 200
    data = response.json()
    parsed_response = TaskHistoryResponse(**data)

    assert len(parsed_response.tasks) == 5
    assert parsed_response.total_tasks == 15
    assert parsed_response.limit == 5
    assert parsed_response.offset == 10

    # Test with offset beyond available tasks
    response = client.get(f"{settings.API_V1_STR}/history?offset=20")
    assert response.status_code == 200
    data = response.json()
    parsed_response = TaskHistoryResponse(**data)

    assert len(parsed_response.tasks) == 0
    assert parsed_response.total_tasks == 15


@pytest.mark.skip("History endpoint not fully implemented yet")
def test_get_history_with_invalid_parameters(client: TestClient):
    """Test that the history endpoint handles invalid parameters properly."""
    # Test with negative limit
    response = client.get(f"{settings.API_V1_STR}/history?limit=-5")
    assert response.status_code == 400

    # Test with negative offset
    response = client.get(f"{settings.API_V1_STR}/history?offset=-5")
    assert response.status_code == 400

    # Test with non-numeric limit
    response = client.get(f"{settings.API_V1_STR}/history?limit=abc")
    assert response.status_code == 400

    # Test with non-numeric offset
    response = client.get(f"{settings.API_V1_STR}/history?offset=xyz")
    assert response.status_code == 400

    # Test with excessively large limit
    response = client.get(f"{settings.API_V1_STR}/history?limit=1000")
    assert response.status_code == 200  # Should accept but cap at configured max
    data = response.json()
    parsed_response = TaskHistoryResponse(**data)
    assert parsed_response.limit <= 100  # Assuming max limit is 100
