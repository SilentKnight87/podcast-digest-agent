import sys
import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
# Remove the old glm_types import
# import google.generativeai.types as glm_types
import google.generativeai as genai
# Keep InvocationContext import for now, might need to mock it later
# from google.adk.context import InvocationContext
# Use BaseAgentEvent if SummarizerAgentEvent doesn't exist yet or adjust import
from agents.base_agent import BaseAgent, BaseAgentEvent, BaseAgentEventType # Assuming base events for now
# from podcast_digest_agent.agents.summarizer_agent import SummarizerAgent, SummarizerAgentEvent, SummarizerAgentEventType # Keep specific agent if defined
from agents.summarizer import SummarizerAgent  # Only import SummarizerAgent
# Remove google.adk.events import as we use BaseAgentEvent now
# from google.adk.events import Event
# from google.generativeai.types import ContentDict, PartDict, GenerationResponse
# Use the new SDK path and alias GenerateContentResponse, include Content and Part
from google.genai.types import ContentDict, PartDict, GenerateContentResponse as GenerationResponse, Content, Part

# Add project root and src directory to sys.path to allow importing src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root) # Keep root just in case
sys.path.insert(0, src_path)     # Add src directory specifically

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# Mock response structure helper removed as we mock stream_generate_content directly

class TestSummarizerAgent:
    """Tests for the SummarizerAgent."""

    @pytest.fixture
    def summarizer_agent(self):
        """Fixture to create a SummarizerAgent instance with mocked dependencies."""
        # Mock the genai.GenerativeModel call within the agent's init
        with patch('src.agents.base_agent.genai.GenerativeModel') as mock_model_init:
            # Configure the mock model instance that the constructor will store
            mock_model_instance = MagicMock()
            # Mock the method that will be called by run_async
            mock_model_instance.generate_content_async = AsyncMock()
            mock_model_init.return_value = mock_model_instance
            
            agent = SummarizerAgent()
            # Attach the mock instances for inspection in tests
            agent._mock_model_init = mock_model_init
            agent._mock_model_instance = mock_model_instance
        return agent

    # Removed @pytest.mark.asyncio as this is not an async test
    def test_summarizer_agent_initialization(self, summarizer_agent):
        """Test if the SummarizerAgent initializes correctly."""
        assert isinstance(summarizer_agent, SummarizerAgent)
        assert isinstance(summarizer_agent, BaseAgent) # Check inheritance
        assert summarizer_agent.name == "SummarizerAgent"
        assert summarizer_agent.instruction is not None # Check default instruction
        # Check if the model was initialized (mocked)
        summarizer_agent._mock_model_init.assert_called_once_with(summarizer_agent.model)
        assert summarizer_agent.llm == summarizer_agent._mock_model_instance

    async def test_summarizer_agent_run_async_basic(self, summarizer_agent):
        """Test the basic run_async functionality with mocked LLM call."""
        input_transcript = "This is a test transcript. It talks about testing agents."
        expected_summary = "Test summary generated."

        # Configure the mock LLM response
        # Create a mock response object that mimics GenerationResponse (aliased)
        mock_llm_response = MagicMock(spec=GenerationResponse)
        
        # Add prompt_feedback attribute that returns None to pass the check
        mock_llm_response.prompt_feedback = None
        
        # Mock the structure to access the text part using PartDict from genai.types
        mock_part = MagicMock(spec=PartDict)
        mock_part.text = expected_summary
        
        # Simulate the response structure: response.candidates[0].content.parts[0].text
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = 1  # FINISH_REASON_STOP = 1
        mock_candidate.content = MagicMock() # Removed spec=ContentDict
        mock_candidate.content.parts = [mock_part]
        mock_llm_response.candidates = [mock_candidate]

        summarizer_agent.llm.generate_content_async.return_value = mock_llm_response

        # Collect events from the async generator
        events = []
        async for event in summarizer_agent.run_async(input_transcript):
            events.append(event)

        # Assertions
        # 1. Check LLM call
        summarizer_agent.llm.generate_content_async.assert_called_once()
        # Get the actual call arguments
        call_args, call_kwargs = summarizer_agent.llm.generate_content_async.call_args
        # Check that the first argument is a Content object
        assert len(call_args) > 0, "LLM call missing arguments"
        assert isinstance(call_args[0], Content), "Input to LLM should be a Content object"
        # Check that the text within the Content object matches the expected prompt structure (basic check)
        assert input_transcript in call_args[0].parts[0].text, "Input transcript not found in LLM call prompt"
        assert summarizer_agent.instruction in call_args[0].parts[0].text, "Agent instruction not found in LLM call prompt"

        # 2. Check yielded events (expect PROGRESS and RESULT)
        assert len(events) == 2, "Expected 2 events (PROGRESS, RESULT)"

        # Check PROGRESS event
        progress_event = events[0]
        assert isinstance(progress_event, BaseAgentEvent), "First event should be BaseAgentEvent"
        assert progress_event.type == BaseAgentEventType.PROGRESS, "First event type should be PROGRESS"
        assert 'status' in progress_event.payload, "PROGRESS event payload missing 'status'"
        assert progress_event.payload['status'] == 'Starting summarization', "PROGRESS status mismatch"

        # Check RESULT event
        result_event = events[1]
        assert isinstance(result_event, BaseAgentEvent), "Second event should be BaseAgentEvent"
        assert result_event.type == BaseAgentEventType.RESULT, "Second event type should be RESULT"
        assert 'summary' in result_event.payload, "RESULT event payload missing 'summary'"
        assert result_event.payload['summary'] == expected_summary, "RESULT summary mismatch"

    async def test_summarizer_agent_run_async(self, summarizer_agent):
        """Test the run_async flow with streaming (Note: run_async currently doesn't stream)."""
        # This test might need adjustments if streaming is implemented in run_async
        # For now, it mirrors the basic test structure as run_async doesn't stream.
        input_transcript = "This is a long transcript... it contains many details... please summarize."
        expected_summary = "Streamed summary part 1 streamed part 2."

        # 1. Prepare Mock LLM Response (mimicking non-streaming for current run_async)
        mock_llm_response = MagicMock(spec=GenerationResponse)
        
        # Add prompt_feedback attribute that returns None to pass the check
        mock_llm_response.prompt_feedback = None
        
        mock_part = MagicMock(spec=PartDict)
        mock_part.text = expected_summary
        mock_candidate = MagicMock()
        mock_candidate.finish_reason = 1  # FINISH_REASON_STOP = 1
        mock_candidate.content = MagicMock() # Removed spec=ContentDict
        mock_candidate.content.parts = [mock_part]
        mock_llm_response.candidates = [mock_candidate]
        summarizer_agent.llm.generate_content_async.return_value = mock_llm_response # Mock non-streaming call

        # 2. Run the Agent
        events = []
        async for event in summarizer_agent.run_async(input_transcript):
            events.append(event)

        # 3. Assertions (similar to basic test)
        # Check LLM call
        summarizer_agent.llm.generate_content_async.assert_called_once()
        call_args, call_kwargs = summarizer_agent.llm.generate_content_async.call_args
        assert isinstance(call_args[0], Content), "Input to LLM should be a Content object"
        assert input_transcript in call_args[0].parts[0].text

        # Check yielded events (expect PROGRESS and RESULT)
        assert len(events) == 2, "Expected 2 events (PROGRESS, RESULT) for non-streaming run_async"
        assert events[0].type == BaseAgentEventType.PROGRESS
        assert events[1].type == BaseAgentEventType.RESULT
        assert events[1].payload['summary'] == expected_summary

# Remove the duplicated test function below this line
# // ... existing code ... (from line 89 to 152) 