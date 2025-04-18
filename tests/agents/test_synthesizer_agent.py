import sys
import os
import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root and src directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
if project_root not in sys.path:
     sys.path.insert(0, project_root) # Keep root just in case

# Import agent and related types
from agents.synthesizer import SynthesizerAgent
from agents.base_agent import BaseAgent, BaseAgentEvent, BaseAgentEventType
from google.genai.types import Content, Part, GenerateContentResponse as GenerationResponse, ContentDict, PartDict

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

class TestSynthesizerAgent:
    """Tests for the SynthesizerAgent."""

    @pytest.fixture
    def synthesizer_agent(self):
        """Fixture to create a SynthesizerAgent instance with mocked dependencies."""
        with patch('src.agents.base_agent.genai.GenerativeModel') as mock_model_init:
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content_async = AsyncMock()
            mock_model_init.return_value = mock_model_instance
            
            agent = SynthesizerAgent()
            agent._mock_model_init = mock_model_init
            agent._mock_model_instance = mock_model_instance
        return agent

    # Removed @pytest.mark.asyncio as this test is synchronous
    def test_synthesizer_agent_initialization(self, synthesizer_agent):
        """Test if the SynthesizerAgent initializes correctly."""
        assert isinstance(synthesizer_agent, SynthesizerAgent)
        assert isinstance(synthesizer_agent, BaseAgent)
        assert synthesizer_agent.name == "SynthesizerAgent"
        assert synthesizer_agent.instruction is not None
        synthesizer_agent._mock_model_init.assert_called_once_with(synthesizer_agent.model)
        assert synthesizer_agent.llm == synthesizer_agent._mock_model_instance

    async def test_synthesizer_agent_run_async_basic(self, synthesizer_agent):
        """Test the basic run_async functionality with mocked LLM call."""
        input_summaries = ["Summary 1 about topic A.", "Summary 2 about topic B."]
        input_summaries_json = json.dumps(input_summaries)
        
        expected_dialogue = [
            {"speaker": "A", "line": "So, regarding topic A..."},
            {"speaker": "B", "line": "Yes, and topic B also came up."}
        ]
        expected_dialogue_json = json.dumps(expected_dialogue)

        # Configure the mock LLM response
        mock_llm_response = MagicMock(spec=GenerationResponse)
        mock_part = MagicMock(spec=PartDict)
        # LLM is expected to return the JSON string in the text part
        mock_part.text = expected_dialogue_json 
        mock_candidate = MagicMock()
        # No spec needed for content after previous experience
        mock_candidate.content = MagicMock() 
        mock_candidate.content.parts = [mock_part]
        # Set a successful finish reason
        mock_candidate.finish_reason = 1 # FINISH_REASON_STOP
        mock_llm_response.candidates = [mock_candidate]
        # Assume no blocking
        mock_llm_response.prompt_feedback = None 
        
        synthesizer_agent.llm.generate_content_async.return_value = mock_llm_response

        # Collect events
        events = []
        async for event in synthesizer_agent.run_async(input_summaries_json):
            events.append(event)

        # Assertions
        # 1. Check LLM call
        synthesizer_agent.llm.generate_content_async.assert_called_once()
        call_args, call_kwargs = synthesizer_agent.llm.generate_content_async.call_args
        assert len(call_args) > 0, "LLM call missing arguments"
        assert isinstance(call_args[0], Content), "Input to LLM should be a Content object"
        # Check if summaries and instruction are in the prompt part
        prompt_text = call_args[0].parts[0].text
        assert synthesizer_agent.instruction in prompt_text, "Instruction missing in prompt"
        assert "Summary 1 about topic A." in prompt_text, "Summary 1 missing in prompt"
        assert "Summary 2 about topic B." in prompt_text, "Summary 2 missing in prompt"
        assert "Dialogue Script (JSON):" in prompt_text, "JSON indicator missing in prompt"

        # 2. Check yielded events (expect PROGRESS and RESULT)
        assert len(events) == 2, f"Expected 2 events (PROGRESS, RESULT), got {len(events)}"

        # Check PROGRESS event
        progress_event = events[0]
        assert isinstance(progress_event, BaseAgentEvent), "First event not BaseAgentEvent"
        assert progress_event.type == BaseAgentEventType.PROGRESS, "First event not PROGRESS"
        assert 'status' in progress_event.payload, "PROGRESS payload missing 'status'"
        assert progress_event.payload['status'] == 'Starting dialogue synthesis', "PROGRESS status mismatch"

        # Check RESULT event
        result_event = events[1]
        assert isinstance(result_event, BaseAgentEvent), "Second event not BaseAgentEvent"
        assert result_event.type == BaseAgentEventType.RESULT, "Second event not RESULT"
        assert 'dialogue' in result_event.payload, "RESULT payload missing 'dialogue' key"
        # The payload should contain the parsed list of dicts
        assert result_event.payload['dialogue'] == expected_dialogue, "Dialogue in RESULT payload mismatch"

    async def test_synthesizer_agent_run_async_invalid_input_json(self, synthesizer_agent):
        """Test run_async with invalid input JSON."""
        input_invalid_json = "this is not json"
        
        events = []
        async for event in synthesizer_agent.run_async(input_invalid_json):
            events.append(event)

        # Expect PROGRESS then ERROR
        assert len(events) == 2, "Expected 2 events (PROGRESS, ERROR)"
        assert events[0].type == BaseAgentEventType.PROGRESS
        assert events[1].type == BaseAgentEventType.ERROR
        assert 'error' in events[1].payload
        assert "Invalid input JSON" in events[1].payload['error']
        # Ensure LLM was not called
        synthesizer_agent.llm.generate_content_async.assert_not_called()

    async def test_synthesizer_agent_run_async_llm_blocked(self, synthesizer_agent):
        """Test run_async when the LLM response is blocked."""
        input_summaries = ["A summary that might trigger filters."]
        input_summaries_json = json.dumps(input_summaries)

        # Configure mock response for blocking
        mock_llm_response = MagicMock(spec=GenerationResponse)
        mock_llm_response.candidates = [] # No candidates when blocked this way
        mock_llm_response.prompt_feedback = MagicMock()
        mock_llm_response.prompt_feedback.block_reason = MagicMock()
        mock_llm_response.prompt_feedback.block_reason.name = "SAFETY"
        mock_llm_response.prompt_feedback.block_reason_message = "Blocked due to safety concerns."
        synthesizer_agent.llm.generate_content_async.return_value = mock_llm_response

        events = []
        async for event in synthesizer_agent.run_async(input_summaries_json):
            events.append(event)

        # Expect PROGRESS then ERROR
        assert len(events) == 2, "Expected 2 events (PROGRESS, ERROR)"
        assert events[0].type == BaseAgentEventType.PROGRESS
        assert events[1].type == BaseAgentEventType.ERROR
        assert 'error' in events[1].payload
        assert "Content blocked by API (SAFETY)" in events[1].payload['error']
        synthesizer_agent.llm.generate_content_async.assert_called_once()

    async def test_synthesizer_agent_run_async_llm_non_json_output(self, synthesizer_agent):
        """Test run_async when the LLM returns text that is not valid JSON."""
        input_summaries = ["Summary 1."]
        input_summaries_json = json.dumps(input_summaries)
        llm_output_text = "Sure, here is the dialogue: Speaker A: Hi!"

        # Configure mock response
        mock_llm_response = MagicMock(spec=GenerationResponse)
        mock_part = MagicMock(spec=PartDict)
        mock_part.text = llm_output_text
        mock_candidate = MagicMock()
        mock_candidate.content = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_candidate.finish_reason = 1
        mock_llm_response.candidates = [mock_candidate]
        mock_llm_response.prompt_feedback = None
        synthesizer_agent.llm.generate_content_async.return_value = mock_llm_response

        events = []
        async for event in synthesizer_agent.run_async(input_summaries_json):
            events.append(event)
        
        # Expect PROGRESS then ERROR
        assert len(events) == 2, "Expected 2 events (PROGRESS, ERROR)"
        assert events[0].type == BaseAgentEventType.PROGRESS
        assert events[1].type == BaseAgentEventType.ERROR
        assert 'error' in events[1].payload
        assert "Failed to parse dialogue script" in events[1].payload['error']
        assert 'raw_response' in events[1].payload
        assert events[1].payload['raw_response'] == llm_output_text
        synthesizer_agent.llm.generate_content_async.assert_called_once()
        
    async def test_synthesizer_agent_run_async_llm_wrong_json_format(self, synthesizer_agent):
        """Test run_async when the LLM returns valid JSON but not the expected list format."""
        input_summaries = ["Summary 1."]
        input_summaries_json = json.dumps(input_summaries)
        # LLM returns a dictionary instead of a list
        llm_output_json = json.dumps({"dialogue": [{"speaker": "A", "line": "Hello"}]})

        # Configure mock response
        mock_llm_response = MagicMock(spec=GenerationResponse)
        mock_part = MagicMock(spec=PartDict)
        mock_part.text = llm_output_json
        mock_candidate = MagicMock()
        mock_candidate.content = MagicMock()
        mock_candidate.content.parts = [mock_part]
        mock_candidate.finish_reason = 1
        mock_llm_response.candidates = [mock_candidate]
        mock_llm_response.prompt_feedback = None
        synthesizer_agent.llm.generate_content_async.return_value = mock_llm_response

        events = []
        async for event in synthesizer_agent.run_async(input_summaries_json):
            events.append(event)
        
        # Expect PROGRESS then ERROR
        assert len(events) == 2, "Expected 2 events (PROGRESS, ERROR)"
        assert events[0].type == BaseAgentEventType.PROGRESS
        assert events[1].type == BaseAgentEventType.ERROR
        assert 'error' in events[1].payload
        assert "LLM response was not in the expected JSON format" in events[1].payload['error']
        assert "Parsed JSON is not a list" in events[1].payload['error']
        assert 'raw_response' in events[1].payload
        assert events[1].payload['raw_response'] == llm_output_json
        synthesizer_agent.llm.generate_content_async.assert_called_once()

    # TODO: Add tests for other error cases (e.g., finish_reason != STOP) 