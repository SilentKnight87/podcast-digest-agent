"""
Tests for ADK pipeline runner.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adk_runners.pipeline_runner import AdkPipelineRunner


class TestAdkPipelineRunner:
    """Test ADK pipeline runner functionality."""

    @pytest.fixture
    def runner(self):
        """Create a runner instance for testing."""
        return AdkPipelineRunner()

    def test_initialization(self, runner):
        """Test pipeline runner initialization."""
        assert runner.session_service is not None
        assert runner.artifact_service is not None
        assert runner.runner is not None

    @pytest.mark.asyncio
    async def test_run_async_success(self, runner):
        """Test successful pipeline execution."""
        video_ids = ["test_video_1", "test_video_2"]
        output_dir = "/test/output"

        # Mock session creation
        mock_session = MagicMock()
        mock_session.id = "test-session-id"
        mock_session.user_id = "system_user"
        mock_session.state = {
            "final_audio_path": "/test/output/podcast_digest_20250126.mp3",
            "dialogue_script": [
                {"speaker": "A", "line": "Welcome!"},
                {"speaker": "B", "line": "Let's begin."},
            ],
            "summaries": ["Summary 1", "Summary 2"],
        }

        with patch.object(
            runner.session_service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_session

            # Mock runner execution
            async def mock_run_async(*args, **kwargs):
                events = [
                    {"type": "agent_started", "agent_name": "TranscriptFetcher"},
                    {"type": "agent_completed", "agent_name": "TranscriptFetcher"},
                    {"type": "agent_started", "agent_name": "SummarizerAgent"},
                    {"type": "agent_completed", "agent_name": "SummarizerAgent"},
                ]
                for event in events:
                    yield event

            with patch.object(runner.runner, "run_async", side_effect=mock_run_async):
                result = await runner.run_async(video_ids, output_dir)

                # Verify result
                assert result["status"] == "success"
                assert result["success"] is True
                assert result["final_audio_path"] == "/test/output/podcast_digest_20250126.mp3"
                assert len(result["dialogue_script"]) == 2
                assert result["summary_count"] == 2
                assert result["transcript_count"] == 2
                assert result["failed_transcripts"] == []
                assert result["error"] is None

    @pytest.mark.asyncio
    async def test_run_async_with_task_id(self, runner):
        """Test pipeline execution with WebSocket support."""
        video_ids = ["test_video"]
        output_dir = "/test/output"
        task_id = "test-task-123"

        mock_session = MagicMock()
        mock_session.id = "test-session-id"
        mock_session.user_id = "system_user"
        mock_session.state = {
            "final_audio_path": "/test/output/podcast_digest_20250126.mp3",
            "dialogue_script": [{"speaker": "A", "line": "Test"}],
            "summaries": ["Test summary"],
        }

        with patch.object(
            runner.session_service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_session

            with patch("src.adk_runners.pipeline_runner.AdkWebSocketBridge") as mock_bridge_class:
                mock_bridge = MagicMock()
                mock_bridge.process_adk_event = AsyncMock()
                mock_bridge_class.return_value = mock_bridge

                async def mock_run_async(*args, **kwargs):
                    events = [
                        {"type": "agent_started", "agent_name": "TranscriptFetcher"},
                        {"type": "tool_called", "tool_name": "fetch_youtube_transcript"},
                        {"type": "agent_completed", "agent_name": "TranscriptFetcher"},
                    ]
                    for event in events:
                        yield event

                with patch.object(runner.runner, "run_async", side_effect=mock_run_async):
                    with patch("src.adk_runners.pipeline_runner.task_manager") as mock_tm:
                        with patch("src.adk_runners.pipeline_runner.settings") as mock_settings:
                            mock_settings.API_V1_STR = "/api/v1"

                            result = await runner.run_async(video_ids, output_dir, task_id)

                            # Verify WebSocket bridge was created and used
                            mock_bridge_class.assert_called_once_with(task_id)
                            assert mock_bridge.process_adk_event.call_count == 3

                            # Verify task manager was updated
                            mock_tm.update_agent_status.assert_called()
                            mock_tm.update_data_flow_status.assert_called()
                            mock_tm.set_task_completed.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_async_no_audio_generated(self, runner):
        """Test handling when no audio file is generated."""
        video_ids = ["test_video"]
        output_dir = "/test/output"

        mock_session = MagicMock()
        mock_session.id = "test-session-id"
        mock_session.user_id = "system_user"
        mock_session.state = {
            "final_audio_path": None,  # No audio generated
            "dialogue_script": [],
            "summaries": [],
        }

        with patch.object(
            runner.session_service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = mock_session

            async def mock_run_async(*args, **kwargs):
                yield {"type": "completed"}

            with patch.object(runner.runner, "run_async", side_effect=mock_run_async):
                result = await runner.run_async(video_ids, output_dir)

                assert result["status"] == "error"
                assert result["success"] is False
                assert result["final_audio_path"] is None
                assert "no audio file was generated" in result["error"]

    @pytest.mark.asyncio
    async def test_run_async_exception_handling(self, runner):
        """Test exception handling in pipeline."""
        video_ids = ["test_video"]
        output_dir = "/test/output"

        with patch.object(
            runner.session_service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = Exception("Session creation failed")

            result = await runner.run_async(video_ids, output_dir)

            assert result["status"] == "error"
            assert result["success"] is False
            assert "Pipeline error: Session creation failed" in result["error"]
            assert result["failed_transcripts"] == video_ids

    @pytest.mark.asyncio
    async def test_run_async_with_task_id_failure(self, runner):
        """Test task failure handling with task_id."""
        video_ids = ["test_video"]
        output_dir = "/test/output"
        task_id = "test-task-456"

        with patch.object(
            runner.session_service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = Exception("Test error")

            with patch("src.adk_runners.pipeline_runner.task_manager") as mock_tm:
                result = await runner.run_async(video_ids, output_dir, task_id)

                # Verify task marked as failed
                mock_tm.set_task_failed.assert_called_once_with(
                    task_id, "Pipeline error: Test error"
                )

    def test_run_pipeline_sync_wrapper(self, runner):
        """Test synchronous wrapper method."""
        video_ids = ["test_video"]

        with patch.object(runner, "run_async", new_callable=AsyncMock) as mock_run_async:
            mock_run_async.return_value = {"status": "success", "success": True}

            result = runner.run_pipeline(video_ids)

            mock_run_async.assert_called_once_with(video_ids, "./output_audio")
            assert result["status"] == "success"

    def test_error_result_creation(self, runner):
        """Test error result structure."""
        error_msg = "Test error message"
        video_ids = ["video1", "video2"]

        result = runner._error_result(error_msg, video_ids)

        assert result["status"] == "error"
        assert result["success"] is False
        assert result["final_audio_path"] is None
        assert result["dialogue_script"] == []
        assert result["summary_count"] == 0
        assert result["transcript_count"] == 0
        assert result["failed_transcripts"] == video_ids
        assert result["error"] == error_msg

    def test_create_summary_from_dialogue(self, runner):
        """Test summary creation from dialogue."""
        dialogue = [
            {"speaker": "A", "line": "Welcome to the podcast!"},
            {"speaker": "B", "line": "Today we discuss AI."},
            {"speaker": "A", "line": "Let's dive in."},
            {"speaker": "B", "line": "Fourth line ignored."},
        ]

        summary = runner._create_summary_from_dialogue(dialogue)

        assert "ADK Generated Summary:" in summary
        assert "A: Welcome to the podcast!" in summary
        assert "B: Today we discuss AI." in summary
        assert "A: Let's dive in." in summary
        assert "Fourth line ignored" not in summary  # Only first 3 lines

    def test_create_summary_from_empty_dialogue(self, runner):
        """Test summary creation from empty dialogue."""
        summary = runner._create_summary_from_dialogue([])
        assert summary == "ADK Generated Summary"

    def test_create_summary_from_none_dialogue(self, runner):
        """Test summary creation from None dialogue."""
        summary = runner._create_summary_from_dialogue(None)
        assert summary == "ADK Generated Summary"
