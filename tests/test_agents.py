"""
Tests for Agent initialization.
"""
import pytest

# Agents to test
from src.agents.base_agent import BaseAgent, DEFAULT_MODEL_ID
from src.agents.transcript_fetcher import TranscriptFetcher
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent

# Tools used by TranscriptFetcher
from src.tools.transcript_tools import fetch_transcript, fetch_transcripts

# Test BaseAgent initialization (though simple)
def test_base_agent_initialization():
    """Test basic initialization of BaseAgent."""
    agent = BaseAgent(name="TestBase", instruction="Do base things.")
    assert agent.name == "TestBase"
    assert agent.instruction == "Do base things."
    assert agent.model == DEFAULT_MODEL_ID # Check default model
    assert agent.tools == [] # Default tools is empty list

def test_transcript_fetcher_initialization():
    """Test initialization of TranscriptFetcher."""
    agent = TranscriptFetcher()
    assert agent.name == "TranscriptFetcher"
    assert "Use the fetch_transcript tool" in agent.instruction
    assert "fetch_transcripts for multiple videos" in agent.instruction
    assert agent.model == DEFAULT_MODEL_ID # Inherited default
    assert len(agent.tools) == 2
    # Check if the correct FunctionTool instances are present
    assert fetch_transcript in agent.tools
    assert fetch_transcripts in agent.tools
    # Verify the names stored on the tool objects within the agent's list
    tool_names = {tool.name for tool in agent.tools}
    assert "_fetch_transcript_impl" in tool_names
    assert "_fetch_transcripts_impl" in tool_names

def test_summarizer_agent_initialization():
    """Test initialization of SummarizerAgent."""
    agent = SummarizerAgent()
    assert agent.name == "SummarizerAgent"
    assert "summarization agent" in agent.instruction
    assert "generate a concise summary" in agent.instruction
    assert agent.model == DEFAULT_MODEL_ID
    assert agent.tools == [] # Expecting no specific tools

def test_synthesizer_agent_initialization():
    """Test initialization of SynthesizerAgent."""
    agent = SynthesizerAgent()
    assert agent.name == "SynthesizerAgent"
    assert "scriptwriting agent" in agent.instruction
    assert "dialogue script" in agent.instruction
    assert "JSON string" in agent.instruction # Verify format instruction
    assert agent.model == DEFAULT_MODEL_ID
    assert agent.tools == [] # Expecting no specific tools

# TODO: Add tests

def test_placeholder():
    """Placeholder test."""
    assert True 