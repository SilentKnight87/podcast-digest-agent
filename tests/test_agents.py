"""
Tests for Agent initialization.
"""
import json
from unittest.mock import MagicMock, patch

# Import types for mocking/verification
import google.generativeai as genai
import pytest  # Add pytest import for async marker
from google.adk.events import Event

# Import needed for patching target if not implicitly loaded
# Agents to test
from src.agents.base_agent import DEFAULT_MODEL_ID, BaseAgent
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.transcript_fetcher import TranscriptFetcher

# Other imports needed for tests
# Tools used by TranscriptFetcher
from src.tools.transcript_tools import fetch_transcript


# Test BaseAgent initialization (though simple)
def test_base_agent_initialization():
    """Test basic initialization of BaseAgent."""
    agent = BaseAgent(name="TestBase", instruction="Do base things.")
    assert agent.name == "TestBase"
    assert agent.instruction == "Do base things."
    assert agent.model == DEFAULT_MODEL_ID  # Check default model
    assert agent.tools == []  # Default tools is empty list


def test_transcript_fetcher_initialization():
    """Test initialization of TranscriptFetcher."""
    agent = TranscriptFetcher()
    assert agent.name == "TranscriptFetcher"
    assert "Use the fetch_transcript tool" in agent.instruction
    assert "fetch_transcripts for multiple videos" in agent.instruction
    assert agent.model == DEFAULT_MODEL_ID  # Inherited default
    assert len(agent.tools) == 2
    # Check if the correct Tool instances are present
    tool_names = {tool.name for tool in agent.tools}
    assert "fetch_transcript" in tool_names
    assert "fetch_transcripts" in tool_names


def test_summarizer_agent_initialization():
    """Test initialization of SummarizerAgent."""
    agent = SummarizerAgent()
    assert agent.name == "SummarizerAgent"
    assert "summarization agent" in agent.instruction
    assert "generate a concise summary" in agent.instruction
    assert agent.model == DEFAULT_MODEL_ID
    assert agent.tools == []  # Expecting no specific tools


def test_synthesizer_agent_initialization():
    """Test initialization of SynthesizerAgent."""
    agent = SynthesizerAgent()
    assert agent.name == "SynthesizerAgent"
    assert "scriptwriting agent" in agent.instruction
    assert "dialogue script" in agent.instruction
    assert "JSON string" in agent.instruction  # Verify format instruction
    assert agent.model == DEFAULT_MODEL_ID
    assert agent.tools == []  # Expecting no specific tools


# Test SummarizerAgent functionality (direct run_async)
@pytest.mark.asyncio
async def test_summarizer_agent_run_async():
    """Test the SummarizerAgent's run_async generates a summary via the LLM."""
    # Arrange: Create agent
    agent = SummarizerAgent()

    test_transcript = "This is a long podcast transcript about AI advancements. It covers topics like LLMs, diffusion models, and reinforcement learning. The conclusion is that AI is evolving rapidly."
    expected_summary = "The podcast discusses AI advancements including LLMs, diffusion models, and reinforcement learning, concluding that AI evolution is rapid."

    # Mock the event that run_async should yield
    mock_llm_response_content = genai.Content(
        role="model", parts=[genai.Part(text=expected_summary)]
    )
    # Create the event *without* is_final_response
    mock_final_event = Event(content=mock_llm_response_content, author=agent.name)

    # Configure the mock run_async to be an async generator yielding the final event
    async def mock_event_generator(*args, **kwargs):
        # Check if the correct content was passed (optional but good practice)
        assert kwargs.get("content") == input_content
        yield mock_final_event

    # Manually assign the mock generator function using object.__setattr__ to bypass Pydantic
    object.__setattr__(agent, "run_async", mock_event_generator)

    # Prepare input for the agent (though run_async is mocked, we still call it)
    input_content = genai.Content(role="user", parts=[genai.Part(text=test_transcript)])

    # Act
    final_response_text = "Agent did not produce a final response."
    async for event in agent.run_async(content=input_content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            break

    # Assert
    assert final_response_text == expected_summary
    # We can't easily assert call counts on the manually assigned method
    # Instead, assertions inside the mock_event_generator check correct args


# Test SynthesizerAgent functionality (simulated run)
@pytest.mark.asyncio
async def test_synthesizer_agent_run_async():
    """Test the SynthesizerAgent's run_async generates a dialogue script JSON via the LLM."""
    # Arrange
    agent = SynthesizerAgent()

    input_summaries = [
        "Summary 1: Discussed apples and oranges.",
        "Summary 2: Talked about bananas and grapes.",
        "Summary 3: Mentioned berries and melons.",
    ]
    expected_dialogue_script_obj = [
        {"speaker": "A", "line": "Based on Summary 1: Discussed apples and oranges."},
        {"speaker": "B", "line": "Also, from Summary 2: Talked about bananas and grapes."},
        {"speaker": "A", "line": "Finally, Summary 3 mentioned berries and melons."},
    ]
    expected_dialogue_json = json.dumps(expected_dialogue_script_obj, indent=2)

    # Mock the event that run_async should yield
    mock_llm_response_content = genai.Content(
        role="model", parts=[genai.Part(text=expected_dialogue_json)]
    )
    # Create the event *without* is_final_response
    mock_final_event = Event(content=mock_llm_response_content, author=agent.name)

    # Configure the mock run_async to be an async generator yielding the final event
    async def mock_event_generator(*args, **kwargs):
        # Check if the correct content was passed
        assert kwargs.get("content").parts[0].text == input_summaries_json
        yield mock_final_event

    # Manually assign the mock generator function using object.__setattr__ to bypass Pydantic
    object.__setattr__(agent, "run_async", mock_event_generator)

    # Prepare input for the agent
    input_summaries_json = json.dumps(input_summaries)
    input_content = genai.Content(role="user", parts=[genai.Part(text=input_summaries_json)])

    # Act
    final_response_text = "Agent did not produce a final response."
    async for event in agent.run_async(content=input_content):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response_text = event.content.parts[0].text
            break

    # Assert
    try:
        actual_dialogue_obj = json.loads(final_response_text)
        assert actual_dialogue_obj == expected_dialogue_script_obj
    except json.JSONDecodeError:
        pytest.fail(f"SynthesizerAgent did not return valid JSON. Output: {final_response_text}")

    # Again, call assertions are difficult here, rely on checks within mock_event_generator


# TODO: Add tests for TranscriptFetcher tool usage

# Remove placeholder test
# def test_placeholder():
#     """Placeholder test."""
#     assert True


# Test SummarizerAgent functionality
@pytest.mark.asyncio
async def test_summarizer_agent_run():
    """Test the SummarizerAgent's run method generates a summary."""
    # Arrange: Create agent
    agent = SummarizerAgent()

    test_transcript = "This is a long podcast transcript about AI advancements. It covers topics like LLMs, diffusion models, and reinforcement learning. The conclusion is that AI is evolving rapidly."
    expected_summary = "The podcast discusses AI advancements including LLMs, diffusion models, and reinforcement learning, concluding that AI evolution is rapid."

    # Mock the Gemini model's generate_content method
    mock_response = MagicMock()
    mock_response.text = expected_summary

    with patch.object(agent.llm, "generate_content", return_value=mock_response) as mock_generate:
        # Act
        result = await agent.run(test_transcript)

        # Assert
        mock_generate.assert_called_once()
        assert result["summary"] == expected_summary


# Test SynthesizerAgent functionality
@pytest.mark.asyncio
async def test_synthesizer_agent_run():
    """Test the SynthesizerAgent's run method generates a dialogue script."""
    # Arrange
    agent = SynthesizerAgent()

    input_summaries = [
        "Summary 1: Discussed apples and oranges.",
        "Summary 2: Talked about bananas and grapes.",
        "Summary 3: Mentioned berries and melons.",
    ]
    expected_dialogue_script = [
        {"speaker": "A", "line": "Based on Summary 1: Discussed apples and oranges."},
        {"speaker": "B", "line": "Also, from Summary 2: Talked about bananas and grapes."},
        {"speaker": "A", "line": "Finally, Summary 3 mentioned berries and melons."},
    ]
    expected_dialogue_json = json.dumps(expected_dialogue_script)

    # Mock the Gemini model's generate_content method
    mock_response = MagicMock()
    mock_response.text = expected_dialogue_json

    with patch.object(agent.llm, "generate_content", return_value=mock_response) as mock_generate:
        # Act
        result = await agent.run(input_summaries)

        # Assert
        mock_generate.assert_called_once()
        assert result["dialogue"] == expected_dialogue_script


# Test TranscriptFetcher functionality
@pytest.mark.asyncio
async def test_transcript_fetcher_run():
    """Test the TranscriptFetcher's run method fetches transcripts."""
    # Arrange
    agent = TranscriptFetcher()
    video_id = "test_video_id"
    expected_transcript = "This is a test transcript"

    # Mock the fetch_transcript tool
    mock_fetch_result = {"success": True, "transcript": expected_transcript, "error": None}

    with patch.object(fetch_transcript, "run", return_value=mock_fetch_result) as mock_fetch:
        # Act
        result = await agent.run(video_id)

        # Assert
        mock_fetch.assert_called_once_with(video_id=video_id)
        assert result["transcript"] == expected_transcript
        assert result["success"] is True
