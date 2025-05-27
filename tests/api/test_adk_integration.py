"""
Tests for ADK integration in API endpoints.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.v1.endpoints.tasks import extract_video_id_from_url, run_adk_processing_pipeline
from src.models.api_models import ProcessUrlRequest


class TestAdkApiIntegration:
    """Test ADK integration with API endpoints."""

    @pytest.mark.asyncio
    async def test_run_adk_processing_pipeline_success(self):
        """Test successful ADK pipeline execution via API."""
        task_id = "test-task-adk"
        request_data = ProcessUrlRequest(youtube_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with patch("src.api.v1.endpoints.tasks.AdkPipelineRunner") as mock_runner_class:
            # Mock ADK pipeline runner
            mock_runner = MagicMock()
            mock_runner.run_async = AsyncMock(
                return_value={
                    "success": True,
                    "final_audio_path": "/output/test_audio.mp3",
                    "dialogue_script": [
                        {"speaker": "A", "line": "Welcome to ADK!"},
                        {"speaker": "B", "line": "This is powered by Google ADK."},
                    ],
                    "summary_count": 2,
                    "transcript_count": 1,
                    "failed_transcripts": [],
                    "error": None,
                }
            )
            mock_runner_class.return_value = mock_runner

            with patch("src.api.v1.endpoints.tasks.task_manager") as mock_tm:
                with patch("src.api.v1.endpoints.tasks.settings") as mock_settings:
                    mock_settings.OUTPUT_AUDIO_DIR = "/output"
                    mock_settings.API_V1_STR = "/api/v1"

                    await run_adk_processing_pipeline(task_id, request_data)

                    # Verify ADK runner was created and called
                    mock_runner_class.assert_called_once()
                    mock_runner.run_async.assert_called_once_with(
                        video_ids=["dQw4w9WgXcQ"], output_dir="/output", task_id=task_id
                    )

                    # Verify task manager was updated
                    mock_tm.update_task_processing_status.assert_called_once()
                    mock_tm.set_task_completed.assert_called_once()

                    # Check completed call arguments
                    complete_call = mock_tm.set_task_completed.call_args
                    assert complete_call[0][0] == task_id
                    assert "ADK Generated Summary" in complete_call[0][1]
                    assert complete_call[0][2] == "/api/v1/audio/test_audio.mp3"

    @pytest.mark.asyncio
    async def test_run_adk_processing_pipeline_invalid_url(self):
        """Test ADK pipeline with invalid YouTube URL."""
        task_id = "test-task-invalid"
        request_data = ProcessUrlRequest(youtube_url="https://not-youtube.com/video")

        with patch("src.api.v1.endpoints.tasks.task_manager") as mock_tm:
            await run_adk_processing_pipeline(task_id, request_data)

            # Should fail with invalid URL
            mock_tm.set_task_failed.assert_called_once()
            fail_call = mock_tm.set_task_failed.call_args
            assert "Could not extract video ID" in fail_call[0][1]

    @pytest.mark.asyncio
    async def test_run_adk_processing_pipeline_adk_failure(self):
        """Test handling of ADK pipeline failure."""
        task_id = "test-task-fail"
        request_data = ProcessUrlRequest(youtube_url="https://www.youtube.com/watch?v=failVideo")

        with patch("src.api.v1.endpoints.tasks.AdkPipelineRunner") as mock_runner_class:
            # Mock ADK pipeline runner with failure
            mock_runner = MagicMock()
            mock_runner.run_async = AsyncMock(
                return_value={
                    "success": False,
                    "final_audio_path": None,
                    "dialogue_script": [],
                    "error": "ADK pipeline test error",
                }
            )
            mock_runner_class.return_value = mock_runner

            with patch("src.api.v1.endpoints.tasks.task_manager") as mock_tm:
                with patch("src.api.v1.endpoints.tasks.settings") as mock_settings:
                    mock_settings.OUTPUT_AUDIO_DIR = "/output"

                    await run_adk_processing_pipeline(task_id, request_data)

                    # Verify task marked as failed
                    mock_tm.set_task_failed.assert_called_with(task_id, "ADK pipeline test error")

    @pytest.mark.asyncio
    async def test_run_adk_processing_pipeline_no_audio_path(self):
        """Test handling when ADK succeeds but doesn't generate audio."""
        task_id = "test-task-no-audio"
        request_data = ProcessUrlRequest(youtube_url="https://youtu.be/testVideo")

        with patch("src.api.v1.endpoints.tasks.AdkPipelineRunner") as mock_runner_class:
            mock_runner = MagicMock()
            mock_runner.run_async = AsyncMock(
                return_value={
                    "success": True,
                    "final_audio_path": None,  # No audio path
                    "dialogue_script": [],
                    "error": None,
                }
            )
            mock_runner_class.return_value = mock_runner

            with patch("src.api.v1.endpoints.tasks.task_manager") as mock_tm:
                with patch("src.api.v1.endpoints.tasks.settings") as mock_settings:
                    mock_settings.OUTPUT_AUDIO_DIR = "/output"

                    await run_adk_processing_pipeline(task_id, request_data)

                    # Should fail with specific error
                    mock_tm.set_task_failed.assert_called_with(
                        task_id, "ADK pipeline succeeded but no audio file was generated"
                    )

    @pytest.mark.asyncio
    async def test_run_adk_processing_pipeline_exception(self):
        """Test exception handling in ADK pipeline."""
        task_id = "test-task-exception"
        request_data = ProcessUrlRequest(youtube_url="https://www.youtube.com/watch?v=testVideo")

        with patch("src.api.v1.endpoints.tasks.AdkPipelineRunner") as mock_runner_class:
            mock_runner_class.side_effect = Exception("ADK initialization error")

            with patch("src.api.v1.endpoints.tasks.task_manager") as mock_tm:
                await run_adk_processing_pipeline(task_id, request_data)

                # Should handle exception gracefully
                mock_tm.set_task_failed.assert_called_once()
                fail_call = mock_tm.set_task_failed.call_args
                assert "ADK initialization error" in fail_call[0][1]

    def test_extract_video_id_various_formats(self):
        """Test video ID extraction from various YouTube URL formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share", "dQw4w9WgXcQ"),
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://not-a-valid-youtube.com/", None),
            ("https://www.youtube.com/", None),
            ("invalid-url", None),
        ]

        for url, expected_id in test_cases:
            result = extract_video_id_from_url(url)
            assert result == expected_id, f"Failed for URL: {url}"
