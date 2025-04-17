import pytest
from unittest.mock import patch, AsyncMock, MagicMock
# Use the alias glm for generative language types
import google.generativeai.types as glm_types
import google.generativeai as genai
# Keep InvocationContext import for now, might need to mock it later
# from google.adk.context import InvocationContext
# Use BaseAgentEvent if SummarizerAgentEvent doesn't exist yet or adjust import
from src.agents.base_agent import BaseAgentEvent, BaseAgentEventType # Assuming base events for now
# from podcast_digest_agent.agents.summarizer_agent import SummarizerAgent, SummarizerAgentEvent, SummarizerAgentEventType # Keep specific agent if defined
from src.agents.summarizer import SummarizerAgent  # Only import SummarizerAgent


# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# Mock response structure helper removed as we mock stream_generate_content directly

class TestSummarizerAgent:
    """Tests for the SummarizerAgent."""

    @pytest.fixture
    def summarizer_agent(self):
        """Fixture to create a SummarizerAgent instance with mocked dependencies."""
        # Create a mock model instance directly
        mock_model = MagicMock()
        # Setup the stream_generate_content method
        mock_model.stream_generate_content = AsyncMock()
        
        # Patch the GenerativeModel class to return our mock
        with patch('google.generativeai.GenerativeModel', return_value=mock_model):
            agent = SummarizerAgent()
            # Ensure the agent's _llm attribute is the mocked instance
            agent._llm = mock_model
        return agent

    async def test_summarizer_agent_run_async(self, summarizer_agent):
        """Test the run_async flow with streaming."""
        input_transcript = "This is a long transcript... it contains many details... please summarize."
        
        # 1. Prepare Input Content object
        mock_input_content = glm_types.Content(
            parts=[glm_types.Part(text=input_transcript)]
        )
        # Create a mock context object that mimics InvocationContext
        # This mock is necessary because BaseAgent.run_async expects it
        mock_context = MagicMock()
        # Set the input content on the context mock
        mock_context.input = [mock_input_content]
        # The BaseAgent uses context.model_copy().agent to access the agent instance
        mock_copy_return = MagicMock()
        mock_copy_return.agent = summarizer_agent
        mock_context.model_copy.return_value = mock_copy_return
        # If BaseAgent needs other context attributes, mock them here.

        # 2. Configure Mock LLM Streaming Response
        mock_async_response = AsyncMock()
        mock_chunks = [
            # Simulate chunks as returned by stream_generate_content
            MagicMock(spec=glm_types.GenerateContentResponse, text="Summary chunk 1"),
            MagicMock(spec=glm_types.GenerateContentResponse, text=" chunk 2."),
        ]
        # Make the async mock iterable and return the chunks
        mock_async_response.__aiter__.return_value = iter(mock_chunks)
        # Assign this async mock to the agent's LLM instance's method
        summarizer_agent._llm.stream_generate_content = mock_async_response

        # 3. Run the Agent
        results = []
        # Pass ONLY the mock context to run_async
        # The context mock now holds the input content
        async for event in summarizer_agent.run_async(mock_context):
            results.append(event)

        # 4. Assertions
        # Check the call to the LLM
        summarizer_agent._llm.stream_generate_content.assert_called_once_with(
            [mock_input_content], stream=True
        )

        # Check the generated events
        assert len(results) >= 2, "Expected at least START and COMPLETE events"

        # Expect START event
        assert isinstance(results[0], BaseAgentEvent), "First event should be BaseAgentEvent"
        assert results[0].type == BaseAgentEventType.START, "First event type should be START"
        assert results[0].data is None, "START event data should be None"

        # Check intermediate PROGRESS events (if agent yields them)
        progress_events = [e for e in results if e.type == BaseAgentEventType.PROGRESS]
        if progress_events:
             # If progress events exist, check their content
             full_progress_data = "".join([p.data for p in progress_events if p.data])
             assert full_progress_data == "Summary chunk 1 chunk 2.", "Concatenated progress data mismatch"

        # Expect COMPLETE event as the last one
        assert isinstance(results[-1], BaseAgentEvent), "Last event should be BaseAgentEvent"
        assert results[-1].type == BaseAgentEventType.COMPLETE, "Last event type should be COMPLETE"
        # The final summary might be accumulated internally and added to the COMPLETE event
        assert results[-1].data == "Summary chunk 1 chunk 2.", "COMPLETE event data mismatch"

# Remove the duplicated test function below this line
# // ... existing code ... (from line 89 to 152) 