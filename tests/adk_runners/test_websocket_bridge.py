"""
Tests for ADK WebSocket bridge.
"""
from unittest.mock import patch

import pytest

from src.adk_runners.websocket_bridge import AdkWebSocketBridge


class TestAdkWebSocketBridge:
    """Test ADK WebSocket bridge functionality."""

    @pytest.fixture
    def bridge(self):
        """Create a bridge instance for testing."""
        return AdkWebSocketBridge("test-task-id")

    def test_initialization(self, bridge):
        """Test bridge initialization."""
        assert bridge.task_id == "test-task-id"
        assert bridge.current_agent is None
        assert len(bridge.agent_mapping) == 4
        assert bridge.agent_progress["transcript-fetcher"] == 0

    @pytest.mark.asyncio
    async def test_agent_started_event(self, bridge):
        """Test handling of agent started event."""
        event = {"type": "agent_started", "agent_name": "TranscriptFetcher"}

        with patch("src.adk_runners.websocket_bridge.task_manager") as mock_tm:
            await bridge.process_adk_event(event)

            # Verify task manager was updated
            mock_tm.update_agent_status.assert_called_once_with(
                task_id="test-task-id",
                agent_id="transcript-fetcher",
                new_status="running",
                progress=10.0,
            )
            mock_tm.add_timeline_event.assert_called_once()

            # Verify internal state
            assert bridge.current_agent == "transcript-fetcher"

    @pytest.mark.asyncio
    async def test_agent_completed_event(self, bridge):
        """Test handling of agent completed event."""
        event = {"type": "agent_completed", "agent_name": "SummarizerAgent"}

        with patch("src.adk_runners.websocket_bridge.task_manager") as mock_tm:
            await bridge.process_adk_event(event)

            # Verify agent marked as completed
            mock_tm.update_agent_status.assert_called_with(
                task_id="test-task-id",
                agent_id="summarizer-agent",
                new_status="completed",
                progress=100.0,
            )

            # Verify overall progress updated
            mock_tm.update_task_processing_status.assert_called_with(
                task_id="test-task-id",
                new_status="processing",
                progress=50,  # Summarizer completion = 50% progress
                current_agent_id="summarizer-agent",
            )

    @pytest.mark.asyncio
    async def test_agent_error_event(self, bridge):
        """Test handling of agent error event."""
        event = {
            "type": "agent_error",
            "agent_name": "AudioGenerator",
            "error": "TTS connection failed",
        }

        with patch("src.adk_runners.websocket_bridge.task_manager") as mock_tm:
            await bridge.process_adk_event(event)

            # Verify error status set
            mock_tm.update_agent_status.assert_called_with(
                task_id="test-task-id", agent_id="audio-generator", new_status="error", progress=0
            )

            # Verify error logged
            mock_tm.add_agent_log.assert_called_with(
                task_id="test-task-id",
                agent_id="audio-generator",
                level="error",
                message="TTS connection failed",
            )

    @pytest.mark.asyncio
    async def test_tool_event_updates_progress(self, bridge):
        """Test that tool events update agent progress."""
        # Set initial agent
        bridge.current_agent = "transcript-fetcher"

        event = {
            "type": "tool_called",
            "tool_name": "fetch_youtube_transcript",
            "agent_name": "TranscriptFetcher",
        }

        with patch("src.adk_runners.websocket_bridge.task_manager") as mock_tm:
            await bridge.process_adk_event(event)

            # Verify progress increased
            assert bridge.agent_progress["transcript-fetcher"] == 20

            mock_tm.update_agent_status.assert_called_with(
                task_id="test-task-id",
                agent_id="transcript-fetcher",
                new_status="running",
                progress=20,
            )

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_cap_progress(self, bridge):
        """Test that multiple tool calls don't exceed 90% progress."""
        bridge.current_agent = "audio-generator"

        # Simulate multiple tool calls
        for i in range(10):
            event = {
                "type": "tool_called",
                "tool_name": "generate_audio_from_dialogue",
                "agent_name": "AudioGenerator",
            }

            with patch("src.core.task_manager"):
                await bridge.process_adk_event(event)

        # Progress should be capped at 90%
        assert bridge.agent_progress["audio-generator"] == 90

    @pytest.mark.asyncio
    async def test_data_flow_updates(self, bridge):
        """Test data flow status updates."""
        event = {"type": "agent_started", "agent_name": "SummarizerAgent"}

        with patch("src.adk_runners.websocket_bridge.task_manager") as mock_tm:
            await bridge.process_adk_event(event)

            # Verify data flow from transcript-fetcher to summarizer
            mock_tm.update_data_flow_status.assert_called_with(
                "test-task-id", "transcript-fetcher", "summarizer-agent", "transferring"
            )

    @pytest.mark.asyncio
    async def test_data_flow_completion(self, bridge):
        """Test data flow marked as completed."""
        event = {"type": "agent_completed", "agent_name": "DialogueSynthesizer"}

        with patch("src.adk_runners.websocket_bridge.task_manager") as mock_tm:
            await bridge.process_adk_event(event)

            # Verify data flow marked as completed
            mock_tm.update_data_flow_status.assert_called_with(
                "test-task-id", "summarizer-agent", "synthesizer-agent", "completed"
            )

    @pytest.mark.asyncio
    async def test_log_event_handling(self, bridge):
        """Test log event processing."""
        event = {
            "type": "log",
            "agent_name": "TranscriptFetcher",
            "level": "info",
            "message": "Fetching transcript for video XYZ",
        }

        with patch("src.adk_runners.websocket_bridge.task_manager") as mock_tm:
            await bridge.process_adk_event(event)

            mock_tm.add_agent_log.assert_called_with(
                task_id="test-task-id",
                agent_id="transcript-fetcher",
                level="info",
                message="Fetching transcript for video XYZ",
            )

    @pytest.mark.asyncio
    async def test_message_event_truncation(self, bridge):
        """Test that long messages are truncated."""
        long_message = "x" * 500
        event = {
            "type": "message",
            "agent_name": "SummarizerAgent",
            "content": f"Progress update: {long_message}",
        }

        with patch("src.adk_runners.websocket_bridge.task_manager") as mock_tm:
            await bridge.process_adk_event(event)

            # Verify message was truncated
            call_args = mock_tm.add_agent_log.call_args[1]
            assert len(call_args["message"]) == 200

    def test_agent_mapping(self, bridge):
        """Test agent name mapping."""
        assert bridge.agent_mapping["TranscriptFetcher"] == "transcript-fetcher"
        assert bridge.agent_mapping["SummarizerAgent"] == "summarizer-agent"
        assert bridge.agent_mapping["DialogueSynthesizer"] == "synthesizer-agent"
        assert bridge.agent_mapping["AudioGenerator"] == "audio-generator"

    def test_overall_progress_calculation(self, bridge):
        """Test overall progress calculation for different agents."""
        assert bridge._calculate_overall_progress("transcript-fetcher") == 25
        assert bridge._calculate_overall_progress("summarizer-agent") == 50
        assert bridge._calculate_overall_progress("synthesizer-agent") == 75
        assert bridge._calculate_overall_progress("audio-generator") == 90
        assert bridge._calculate_overall_progress("unknown-agent") == 0
