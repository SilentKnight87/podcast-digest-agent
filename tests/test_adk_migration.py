"""
Tests for ADK migration components.
"""
from unittest.mock import patch

import pytest

from src.adk_agents import root_agent
from src.adk_runners.pipeline_runner import AdkPipelineRunner
from src.adk_tools.transcript_tools import fetch_youtube_transcript


class TestAdkMigration:
    """Test suite for ADK migration."""

    def test_agent_initialization(self):
        """Test that ADK agents initialize correctly."""
        assert root_agent.name == "PodcastDigestCoordinator"
        assert root_agent.model == "gemini-2.5-flash-preview-04-17"
        assert len(root_agent.sub_agents) == 4

    def test_transcript_tool(self):
        """Test transcript tool functionality."""
        with patch("src.adk_tools.transcript_tools.YouTubeTranscriptApi") as mock_api:
            # Mock successful transcript
            mock_api.get_transcript.return_value = [
                {"text": "Hello world", "start": 0.0, "duration": 2.0}
            ]

            result = fetch_youtube_transcript("test_video_id")

            assert result["success"] is True
            assert result["video_id"] == "test_video_id"
            assert "Hello world" in result["transcript"]

    @pytest.mark.asyncio
    async def test_pipeline_runner_initialization(self):
        """Test ADK pipeline runner initialization."""
        runner = AdkPipelineRunner()

        assert runner.runner is not None
        assert runner.session_service is not None
        assert runner.artifact_service is not None

    def test_agent_structure(self):
        """Test that agent structure matches ADK patterns."""
        # Verify sub-agents
        sub_agent_names = {agent.name for agent in root_agent.sub_agents}
        expected_names = {
            "TranscriptFetcher",
            "SummarizerAgent",
            "DialogueSynthesizer",
            "AudioGenerator",
        }

        assert sub_agent_names == expected_names
