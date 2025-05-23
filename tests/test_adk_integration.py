"""
Integration tests for ADK pipeline with API endpoints.
"""
import pytest
import logging
from fastapi.testclient import TestClient
from src.main import app

logger = logging.getLogger(__name__)
client = TestClient(app)

def test_adk_pipeline_api_integration():
    """Test ADK pipeline integration with API endpoints."""
    
    # Submit a processing request
    response = client.post(
        "/api/v1/process_youtube_url",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    
    assert response.status_code == 202
    task_data = response.json()
    assert "task_id" in task_data
    
    task_id = task_data["task_id"]
    
    # Check task status (may need to wait for completion in real test)
    status_response = client.get(f"/api/v1/status/{task_id}")
    assert status_response.status_code == 200
    
    status_data = status_response.json()
    assert status_data["task_id"] == task_id
    
    logger.info("✅ ADK API integration test passed")