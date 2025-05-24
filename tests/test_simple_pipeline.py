import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to sys.path to allow importing src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.runners.simple_pipeline import SimplePipeline


@pytest.mark.asyncio
class TestSimplePipeline:
    """Test cases for SimplePipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.pipeline = SimplePipeline()

    @patch("src.runners.simple_pipeline.fetch_transcripts")
    async def test_simple_pipeline_imports_and_initializes(self, mock_fetch_transcripts):
        """Test that SimplePipeline can be imported and initialized."""
        # Test initialization
        assert self.pipeline is not None
        assert hasattr(self.pipeline, "transcript_fetcher")
        assert hasattr(self.pipeline, "summarizer")
        assert hasattr(self.pipeline, "synthesizer")
        assert hasattr(self.pipeline, "audio_generator")

    @patch("src.runners.simple_pipeline.texttospeech_v1.TextToSpeechAsyncClient")
    @patch("src.runners.simple_pipeline.combine_audio_segments_tool")
    @patch("src.runners.simple_pipeline.generate_audio_segment_tool")
    @patch("src.runners.simple_pipeline.fetch_transcripts")
    async def test_run_async_no_transcripts(
        self, mock_fetch_transcripts, mock_generate_tool, mock_combine_tool, mock_tts_client
    ):
        """Test run_async when no transcripts are fetched."""
        # Setup mocks
        mock_fetch_transcripts.run.return_value = {"v1": {"success": False}}

        # Execute
        result = await self.pipeline.run_async(["v1"], "./output")

        # Verify
        assert result["success"] is False
        assert result["error"] == "No transcripts fetched"
        assert result["status"] == "error"

    @patch("src.runners.simple_pipeline.texttospeech_v1.TextToSpeechAsyncClient")
    @patch("src.runners.simple_pipeline.combine_audio_segments_tool")
    @patch("src.runners.simple_pipeline.generate_audio_segment_tool")
    @patch("src.runners.simple_pipeline.fetch_transcripts")
    async def test_run_async_with_transcripts_success(
        self, mock_fetch_transcripts, mock_generate_tool, mock_combine_tool, mock_tts_client
    ):
        """Test run_async with successful transcript processing."""
        # Setup mocks
        mock_fetch_transcripts.run.return_value = {
            "v1": {"success": True, "transcript": "Test transcript"}
        }

        # Mock the summarizer agent
        async def mock_summarizer_run(*args, **kwargs):
            mock_event = MagicMock()
            mock_event.type.name = "RESULT"
            mock_event.payload = {"summary": "Test summary"}
            yield mock_event

        self.pipeline.summarizer.run_async = mock_summarizer_run

        # Mock the synthesizer agent
        async def mock_synthesizer_run(*args, **kwargs):
            mock_event = MagicMock()
            mock_event.type.name = "RESULT"
            mock_event.payload = {"dialogue": [{"speaker": "A", "line": "Test line"}]}
            yield mock_event

        self.pipeline.synthesizer.run_async = mock_synthesizer_run

        # Mock audio generation tools
        mock_generate_tool.run = AsyncMock(return_value="segment.mp3")
        mock_combine_tool.run = AsyncMock(return_value="final.mp3")

        # Mock TTS client
        mock_client = AsyncMock()
        mock_tts_client.return_value.__aenter__.return_value = mock_client

        # Execute
        result = await self.pipeline.run_async(["v1"], "./output")

        # Verify
        assert result["success"] is True
        assert result["final_audio_path"] == "final.mp3"
        assert result["status"] == "success"

    def test_error_result_format(self):
        """Test _error_result method format."""
        result = self.pipeline._error_result("Test error", ["v1", "v2"])

        expected = {
            "status": "error",
            "success": False,
            "dialogue_script": [],
            "final_audio_path": None,
            "summary_count": 0,
            "failed_transcripts": ["v1", "v2"],
            "error": "Test error",
        }

        assert result == expected

    def test_extract_successful_transcripts(self):
        """Test _extract_successful_transcripts method."""
        results = {
            "v1": {"success": True, "transcript": "Transcript 1"},
            "v2": {"success": False, "error": "Failed"},
            "v3": {"success": True, "transcript": "Transcript 3"},
            "v4": {"success": True, "transcript": ""},  # Empty transcript
        }

        transcripts = self.pipeline._extract_successful_transcripts(results)

        expected = {"v1": "Transcript 1", "v3": "Transcript 3"}
        assert transcripts == expected

    def test_run_pipeline_sync_wrapper(self):
        """Test the synchronous wrapper."""
        with patch.object(self.pipeline, "run_async") as mock_run_async:
            expected_result = {"status": "success", "success": True}
            mock_run_async.return_value = expected_result

            with patch("asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = expected_result

                result = self.pipeline.run_pipeline(["v1"])

                mock_asyncio_run.assert_called_once()
                assert result == expected_result