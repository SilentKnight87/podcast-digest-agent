"""
Tests for ADK podcast agent.
"""

from src.adk_agents.podcast_agent import (
    audio_agent,
    root_agent,
    summarizer_agent,
    synthesizer_agent,
    transcript_agent,
)


class TestAgentConfiguration:
    """Test agent configurations."""

    def test_root_agent_configuration(self):
        """Test root agent has correct configuration."""
        assert root_agent.name == "PodcastDigestCoordinator"
        assert root_agent.model == "gemini-2.5-flash-preview-04-17"
        assert len(root_agent.sub_agents) == 4
        assert "coordinator for podcast digest generation" in root_agent.instruction.lower()

    def test_transcript_agent_configuration(self):
        """Test transcript agent configuration."""
        assert transcript_agent.name == "TranscriptFetcher"
        assert transcript_agent.model == "gemini-2.5-flash-preview-04-17"
        assert len(transcript_agent.tools) == 2
        assert "transcript" in transcript_agent.description.lower()

    def test_summarizer_agent_configuration(self):
        """Test summarizer agent configuration."""
        assert summarizer_agent.name == "SummarizerAgent"
        assert summarizer_agent.model == "gemini-2.5-flash-preview-04-17"
        assert summarizer_agent.output_key == "summaries"
        assert "summarize" in summarizer_agent.description.lower()

    def test_synthesizer_agent_configuration(self):
        """Test synthesizer agent configuration."""
        assert synthesizer_agent.name == "DialogueSynthesizer"
        assert synthesizer_agent.model == "gemini-2.5-flash-preview-04-17"
        assert synthesizer_agent.output_key == "dialogue_script"
        assert "dialogue" in synthesizer_agent.description.lower()

    def test_audio_agent_configuration(self):
        """Test audio agent configuration."""
        assert audio_agent.name == "AudioGenerator"
        assert audio_agent.model == "gemini-2.5-flash-preview-04-17"
        assert len(audio_agent.tools) == 1
        assert audio_agent.output_key == "final_audio_path"
        assert "audio" in audio_agent.description.lower()

    def test_sub_agents_order(self):
        """Test sub-agents are in correct pipeline order."""
        sub_agent_names = [agent.name for agent in root_agent.sub_agents]
        expected_order = [
            "TranscriptFetcher",
            "SummarizerAgent",
            "DialogueSynthesizer",
            "AudioGenerator",
        ]
        assert sub_agent_names == expected_order

    def test_agent_instructions_quality(self):
        """Test that agent instructions are detailed."""
        agents = [transcript_agent, summarizer_agent, synthesizer_agent, audio_agent, root_agent]

        for agent in agents:
            # Check instruction length (should be detailed)
            assert len(agent.instruction) > 100, f"{agent.name} instruction too short"

            # Check instruction contains key responsibilities
            assert "1." in agent.instruction or "role" in agent.instruction.lower()

    def test_dialogue_format_in_synthesizer(self):
        """Test synthesizer agent has JSON format example."""
        assert "JSON" in synthesizer_agent.instruction
        assert '"speaker"' in synthesizer_agent.instruction
        assert '"line"' in synthesizer_agent.instruction
        assert "[" in synthesizer_agent.instruction  # Array format

    def test_tools_assignment(self):
        """Test tools are correctly assigned to agents."""
        # Transcript agent should have transcript tools
        tool_names = [tool.__name__ for tool in transcript_agent.tools]
        assert "fetch_youtube_transcript" in tool_names
        assert "process_multiple_transcripts" in tool_names

        # Audio agent should have audio generation tool
        audio_tool_names = [tool.__name__ for tool in audio_agent.tools]
        assert "generate_audio_from_dialogue" in audio_tool_names

        # Summarizer and synthesizer should have no tools
        assert len(summarizer_agent.tools) == 0
        assert len(synthesizer_agent.tools) == 0
