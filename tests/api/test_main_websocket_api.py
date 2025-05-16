import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect
from unittest.mock import patch, AsyncMock # AsyncMock for async methods

from src.main import app # FastAPI app
from src.config.settings import settings
from src.core import task_manager
from src.core.connection_manager import manager as ws_manager # WebSocket manager
from src.models.api_models import ProcessUrlRequest, TaskStatusResponse
from pydantic import HttpUrl

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def reset_stores_for_ws_tests():
    """Clears task store and connection manager active connections."""
    task_manager._tasks_store.clear()
    # ws_manager.active_connections.clear() # Assuming direct access for reset is okay for tests
    # More robust: provide a reset method in ConnectionManager if direct access is frowned upon
    # For now, let's create a new manager instance for each test run or clear it carefully.
    original_active_connections = ws_manager.active_connections
    ws_manager.active_connections = {}
    yield
    ws_manager.active_connections = original_active_connections # Restore original ref, though content was cleared
    task_manager._tasks_store.clear()

@pytest.mark.asyncio # Pytest needs this for async test functions
async def test_websocket_connect_disconnect(client: TestClient):
    task_id = "ws-task-connect-disconnect"
    # Ensure task exists for initial status send, or test how endpoint handles non-existent tasks on connect
    task_manager.add_new_task(HttpUrl("http://example.com/video"), ProcessUrlRequest(youtube_url="http://example.com/video"))

    with client.websocket_connect(f"{settings.API_V1_STR}/ws/status/{task_id}") as websocket:
        # Connection should be registered
        assert task_id in ws_manager.active_connections
        assert websocket in ws_manager.active_connections[task_id]
        
        # Test receiving initial status (if task exists and is sent immediately)
        try:
            initial_data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0) 
            assert initial_data["task_id"] == task_id
            assert initial_data["processing_status"]["status"] == "queued"
        except asyncio.TimeoutError:
            pytest.fail("WebSocket did not receive initial status in time.")
        except WebSocketDisconnect:
            pytest.fail("WebSocket disconnected unexpectedly during initial status receive.")

    # After context manager exits, disconnect should have been called
    # Need a brief moment for the server-side disconnect logic to run if it's in a finally block
    await asyncio.sleep(0.01) 
    assert task_id not in ws_manager.active_connections 

@pytest.mark.asyncio
async def test_websocket_initial_status_non_existent_task(client: TestClient):
    task_id = "ws-task-non-existent"
    # Task does NOT exist in task_manager
    
    with client.websocket_connect(f"{settings.API_V1_STR}/ws/status/{task_id}") as websocket:
        # The current implementation in main.py logs a warning if task not found,
        # and client waits for updates. It doesn't send a specific "not_found" message yet.
        # So, we might not receive an initial message, or it might be an empty ack.
        # For this test, we verify it connects and doesn't crash.
        # We might not get an immediate JSON if the task isn't found and no message is sent.
        # Let's check if the connection is active, implying it didn't close due to error.
        assert task_id in ws_manager.active_connections
        # Attempting to receive with a short timeout to see if anything is sent.
        # If the spec was to send a specific message on task not found, we would assert that.
        try:
            await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
            # If it sends something, this test might need adjustment based on what that is.
        except asyncio.TimeoutError:
            # This is expected if no message is sent for a non-existent task initially
            pass 
    await asyncio.sleep(0.01)
    assert task_id not in ws_manager.active_connections

@pytest.mark.asyncio
async def test_websocket_receives_updates(client: TestClient):
    task_id = "ws-task-updates"
    video_url = HttpUrl("http://example.com/video-updates")
    task_manager.add_new_task(video_url, ProcessUrlRequest(youtube_url=video_url))

    with client.websocket_connect(f"{settings.API_V1_STR}/ws/status/{task_id}") as websocket:
        # 1. Receive initial status
        initial_data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
        assert initial_data["task_id"] == task_id
        assert initial_data["processing_status"]["status"] == "queued"

        # 2. Trigger an update in task_manager that should broadcast
        # Using patch to make ws_manager.broadcast_to_task awaitable if it's called by a sync wrapper
        # However, schedule_broadcast runs it in a new task. So we need to ensure that task completes.
        
        # Mock `_broadcast_task_update` to capture its call and ensure it can run
        # This is tricky because it's scheduled via asyncio.create_task from a sync function.
        # For a robust test, we might need to make the task_manager functions async
        # or use a more sophisticated way to await scheduled tasks in tests.
        
        # For now, let's directly call the update and then poll the websocket.
        # The `schedule_broadcast` will attempt to run `_broadcast_task_update`.
        
        task_manager.update_agent_status(task_id, "transcript-fetcher", "running", progress=50.0)
        
        # Wait for the update to be pushed
        try:
            updated_data_agent = await asyncio.wait_for(websocket.receive_json(), timeout=2.0) # Increased timeout
            assert updated_data_agent["task_id"] == task_id
            found_agent = False
            for agent in updated_data_agent["agents"]:
                if agent["id"] == "transcript-fetcher":
                    assert agent["status"] == "running"
                    assert agent["progress"] == 50.0
                    found_agent = True
                    break
            assert found_agent, "Transcript fetcher agent update not found or incorrect."
        except asyncio.TimeoutError:
            pytest.fail("WebSocket did not receive agent status update in time.")

        # 3. Trigger another update (e.g., task completion)
        task_manager.set_task_completed(task_id, "Test summary", "/api/v1/audio/test.mp3")
        try:
            updated_data_completed = await asyncio.wait_for(websocket.receive_json(), timeout=2.0)
            assert updated_data_completed["task_id"] == task_id
            assert updated_data_completed["processing_status"]["status"] == "completed"
            assert updated_data_completed["summary_text"] == "Test summary"
        except asyncio.TimeoutError:
            pytest.fail("WebSocket did not receive task completion update in time.")

@pytest.mark.asyncio
async def test_websocket_ping_pong(client: TestClient):
    task_id = "ws-task-ping"
    task_manager.add_new_task(HttpUrl("http://example.com/video-ping"), ProcessUrlRequest(youtube_url="http://example.com/video-ping"))

    with client.websocket_connect(f"{settings.API_V1_STR}/ws/status/{task_id}") as websocket:
        await asyncio.wait_for(websocket.receive_json(), timeout=1.0) # Consume initial status
        
        await websocket.send_text("ping")
        response = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
        assert response == "pong"

@pytest.mark.asyncio
async def test_websocket_multiple_clients_receive_updates(client: TestClient):
    task_id = "ws-task-multi-client"
    video_url = HttpUrl("http://example.com/video-multi")
    task_manager.add_new_task(video_url, ProcessUrlRequest(youtube_url=video_url))

    with client.websocket_connect(f"{settings.API_V1_STR}/ws/status/{task_id}") as ws1, \
         client.websocket_connect(f"{settings.API_V1_STR}/ws/status/{task_id}") as ws2:
        
        # Consume initial status from both
        initial_data1 = await asyncio.wait_for(ws1.receive_json(), timeout=1.0)
        initial_data2 = await asyncio.wait_for(ws2.receive_json(), timeout=1.0)
        assert initial_data1["task_id"] == task_id
        assert initial_data2["task_id"] == task_id

        # Trigger an update
        task_manager.update_task_processing_status(task_id, "processing", progress=75.0, current_agent_id="summarizer-agent")

        # Check update on ws1
        updated_data_ws1 = await asyncio.wait_for(ws1.receive_json(), timeout=2.0)
        assert updated_data_ws1["processing_status"]["status"] == "processing"
        assert updated_data_ws1["processing_status"]["overall_progress"] == 75.0

        # Check update on ws2
        updated_data_ws2 = await asyncio.wait_for(ws2.receive_json(), timeout=2.0)
        assert updated_data_ws2["processing_status"]["status"] == "processing"
        assert updated_data_ws2["processing_status"]["overall_progress"] == 75.0

    await asyncio.sleep(0.01) # Allow disconnects to process
    assert task_id not in ws_manager.active_connections 