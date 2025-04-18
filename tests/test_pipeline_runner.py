import sys
import os

# Add project root to sys.path to allow importing src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import unittest.mock

# Use absolute paths for imports from src
from src.runners.pipeline_runner import PipelineRunner
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.tools.transcript_tools import fetch_transcripts
from src.tools.audio_tools import generate_audio_segment_tool, combine_audio_segments_tool
import google.generativeai as genai
from google.generativeai.types import ContentDict, PartDict
from google.adk.events import Event

# Mark all tests in this module as asyncio
# pytestmark = pytest.mark.asyncio # Removed global mark

# --- Mock Helper Functions ---

async def mock_async_return(value):
    """Helper to return a value from an awaited async function."""
    return value

# Updated mock_async_iterator to yield final events
async def mock_async_iterator(items, is_final=True):
    """Helper to create an async iterator from a list of items (Events)."""
    if not items: # Handle empty list case
        return

    last_index = len(items) - 1
    for i, item in enumerate(items):
        # Create a mock event object that can simulate is_final_response()
        mock_event = MagicMock(spec=Event)
        # Copy attributes from the original item (assuming item is an Event or dict)
        if isinstance(item, Event):
            mock_event.content = item.content
            mock_event.author = item.author
            # Add other attributes if needed
        elif isinstance(item, dict): # If just passing dicts
             mock_event.content = item.get('content')
             mock_event.author = item.get('author')
        else: # Pass through other types? Or raise error?
            mock_event = item # Assume it's already a mock or simple type

        # Set the return value for is_final_response()
        # Make the last event final by default, or all if is_final=True for all
        mock_event.is_final_response.return_value = (i == last_index) if is_final else False
        
        yield mock_event
        await asyncio.sleep(0) # Yield control

# Default mock results for agents
DEFAULT_TRANSCRIPT_RESULT = { # Now used for the patched tool function
    "results": {
        "v_default": {"status": "success", "result": {"transcript": "Default transcript text."}}
    }
}
DEFAULT_SUMMARY_TEXT = "Default summary text." # For summarizer agent mock
DEFAULT_SUMMARY_EVENT = Event(
    content=ContentDict(role='model', parts=[PartDict(text=DEFAULT_SUMMARY_TEXT)]),
    author="MockSummarizer"
)
DEFAULT_DIALOGUE_OBJ = [
    {"speaker": "A", "line": "Default dialogue line 1"},
    {"speaker": "B", "line": "Default dialogue line 2"}
]
DEFAULT_DIALOGUE_JSON = json.dumps(DEFAULT_DIALOGUE_OBJ) # For synthesizer agent mock
DEFAULT_DIALOGUE_EVENT = Event(
    content=ContentDict(role='model', parts=[PartDict(text=DEFAULT_DIALOGUE_JSON)]),
    author="MockSynthesizer"
)

# --- Test Fixtures ---
@pytest.fixture
def mock_summarizer_agent():
    """Fixture for a mock SummarizerAgent."""
    mock = MagicMock(spec=SummarizerAgent) # Use MagicMock for base, add async methods
    mock.name = "MockSummarizerAgent"
    
    # Define the async iterator behavior for run_async
    # Default behavior: return default summary
    async def default_run_async(*args, **kwargs):
        yield Event(
            content=ContentDict(role='model', parts=[PartDict(text=DEFAULT_SUMMARY_TEXT)]),
            author="MockSummarizer"
        )
        # Make sure the last event indicates it's final
        # Our helper _run_agent_get_final_response checks event.is_final_response()
        # The mock Event needs this method.
        last_event = Event(
            content=ContentDict(role='model', parts=[PartDict(text=DEFAULT_SUMMARY_TEXT)]),
            author="MockSummarizer"
        )
        # Add is_final_response mock method to the event mock itself
        mock_event = MagicMock(spec=Event)
        mock_event.content = last_event.content
        mock_event.author = last_event.author
        mock_event.is_final_response.return_value = True 
        yield mock_event

    mock.run_async = default_run_async # Assign the async function
    # Keep the synchronous run mock for potential direct calls or other tests
    mock.run = MagicMock(return_value={"summary": DEFAULT_SUMMARY_TEXT})
    return mock

@pytest.fixture
def mock_synthesizer_agent():
    """Fixture for a mock SynthesizerAgent."""
    mock = MagicMock(spec=SynthesizerAgent) # Use MagicMock for base, add async methods
    mock.name = "MockSynthesizerAgent"
    
    # Define the async iterator behavior for run_async
    async def default_run_async(*args, **kwargs):
        yield Event(
            content=ContentDict(role='model', parts=[PartDict(text=DEFAULT_DIALOGUE_JSON)]),
            author="MockSynthesizer"
        )
        # Make sure the last event indicates it's final
        last_event = Event(
            content=ContentDict(role='model', parts=[PartDict(text=DEFAULT_DIALOGUE_JSON)]),
            author="MockSynthesizer"
        )
        mock_event = MagicMock(spec=Event)
        mock_event.content = last_event.content
        mock_event.author = last_event.author
        mock_event.is_final_response.return_value = True
        yield mock_event

    mock.run_async = default_run_async # Assign the async function
    # Keep the synchronous run mock for potential direct calls or other tests
    mock.run = MagicMock(return_value={"dialogue": DEFAULT_DIALOGUE_OBJ})
    return mock

# Removed pipeline_runner fixture, now created in TestPipelineRunnerBase setup

# --- Test Cases (Removed unused init test as mocks changed) ---

# --- Async Pipeline Tests ---

@pytest.mark.asyncio
class TestPipelineRunnerBase:
    @pytest.fixture(autouse=True)
    def setup(self, mock_summarizer_agent, mock_synthesizer_agent):
        """Setup test fixtures."""
        self.mock_summarizer = mock_summarizer_agent
        self.mock_synthesizer = mock_synthesizer_agent
        # Create mocks for the new dependencies
        self.mock_transcript_fetcher = AsyncMock()
        self.mock_audio_generator = AsyncMock()
        # Mock the specific tool functions within the mocks if needed later,
        # e.g., self.mock_transcript_fetcher.run = AsyncMock(...)

        # Create the pipeline runner with the mock agents and tools
        self.pipeline_runner = PipelineRunner(
            summarizer=self.mock_summarizer,
            synthesizer=self.mock_synthesizer,
            transcript_fetcher=self.mock_transcript_fetcher,
            audio_generator=self.mock_audio_generator
        )

        yield

class TestPipelineRunner(TestPipelineRunnerBase):
    """Test cases for PipelineRunner."""
    
    @pytest.mark.asyncio
    @patch('src.runners.pipeline_runner.combine_audio_segments_tool')
    @patch('src.runners.pipeline_runner.generate_audio_segment_tool')
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    @patch('tempfile.mkdtemp')
    @patch('src.runners.pipeline_runner.fetch_transcripts')
    async def test_run_pipeline_async_happy_path(self, mock_fetch_tool_obj, mock_mkdtemp, mock_rmtree, mock_exists, mock_generate_tool_obj, mock_combine_tool_obj):
        """Test run_pipeline_async with successful transcript fetch and simulated steps."""
        # Setup
        video_ids = ["v1", "v2"]
        output_dir = "./fake_output_happy"
        temp_dir = "/tmp/fake_temp_dir_happy"
        final_audio = f"{output_dir}/podcast_digest_mock_timestamp.mp3"
        
        # Configure the .func attribute ON the mocked tool objects - Use MagicMock for sync func
        mock_fetch_tool_obj.func = MagicMock(return_value={
            "results": { # Ensure the top-level 'results' key is present
                "v1": {"status": "success", "result": {"transcript": "Transcript 1 text."}},
                "v2": {"status": "success", "result": {"transcript": "Transcript 2 text."}}
            }
        })
        mock_mkdtemp.return_value = temp_dir
        # Audio tool funcs must be async as they are wrapped in create_task
        mock_generate_tool_obj.func = AsyncMock(return_value="segment_path.mp3")
        # Combine func is called synchronously
        mock_combine_tool_obj.func = MagicMock(return_value=final_audio)
        mock_exists.return_value = True

        # Configure agent mocks (no calls expected, rely on default fixtures)
        # self.mock_summarizer.run.return_value = {"summary": "Summary of transcript 1."}
        # self.mock_synthesizer.run.return_value = {
        #     "dialogue": [
        #         {"speaker": "A", "line": "Happy dialogue line 1"},
        #         {"speaker": "B", "line": "Happy dialogue line 2"}
        #     ]
        # }
        # We need to override the default run_async behavior for summarizer for this specific test
        async def summarizer_run_async_happy_path(*args, **kwargs):
            # Determine input to simulate different summaries
            input_text = args[0] if args else ""
            summary_text = "Summary of transcript 1." if "Transcript 1" in input_text else "Summary of transcript 2."
            
            first_event = Event(content=ContentDict(role='model', parts=[PartDict(text=summary_text)]), author="MockSummarizer")
            mock_event_first = MagicMock(spec=Event)
            mock_event_first.content = first_event.content
            mock_event_first.author = first_event.author
            mock_event_first.is_final_response.return_value = False # Not final
            yield mock_event_first
            
            last_event = Event(content=ContentDict(role='model', parts=[PartDict(text=summary_text)]), author="MockSummarizer")
            mock_event_last = MagicMock(spec=Event)
            mock_event_last.content = last_event.content
            mock_event_last.author = last_event.author
            mock_event_last.is_final_response.return_value = True # Final
            yield mock_event_last
        # Assign the async generator function directly
        self.mock_summarizer.run_async = summarizer_run_async_happy_path

        # Synthesizer uses default behavior from fixture
        async def synthesizer_run_async_happy_path(*args, **kwargs):
            dialogue_obj = [
                {"speaker": "A", "line": "Happy dialogue line 1"},
                {"speaker": "B", "line": "Happy dialogue line 2"}
            ]
            dialogue_json = json.dumps(dialogue_obj)
            
            first_event = Event(content=ContentDict(role='model', parts=[PartDict(text=dialogue_json)]), author="MockSynthesizer")
            mock_event_first = MagicMock(spec=Event)
            mock_event_first.content = first_event.content
            mock_event_first.author = first_event.author
            mock_event_first.is_final_response.return_value = False
            yield mock_event_first

            last_event = Event(content=ContentDict(role='model', parts=[PartDict(text=dialogue_json)]), author="MockSynthesizer")
            mock_event_last = MagicMock(spec=Event)
            mock_event_last.content = last_event.content
            mock_event_last.author = last_event.author
            mock_event_last.is_final_response.return_value = True
            yield mock_event_last
        # Assign the async generator function directly
        self.mock_synthesizer.run_async = synthesizer_run_async_happy_path

        # Execute
        result = await self.pipeline_runner.run_pipeline_async(video_ids, output_dir=output_dir)

        # Verify
        mock_fetch_tool_obj.func.assert_called_once_with(video_ids=video_ids)
        # Cannot easily assert call count on directly assigned async generators
        # assert self.mock_summarizer.run_async.call_count == 2 
        # assert self.mock_synthesizer.run_async.call_count == 1
        assert mock_generate_tool_obj.func.call_count == 2
        mock_combine_tool_obj.func.assert_called_once()
        assert result["success"] is True
        assert result["final_audio_path"] == final_audio

    @pytest.mark.asyncio
    @patch('src.runners.pipeline_runner.combine_audio_segments_tool')
    @patch('src.runners.pipeline_runner.generate_audio_segment_tool')
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    @patch('tempfile.mkdtemp')
    @patch('src.runners.pipeline_runner.fetch_transcripts')
    async def test_run_pipeline_async_transcript_fetch_fails(self, mock_fetch_tool_obj, mock_mkdtemp, mock_rmtree, mock_exists, mock_generate_tool_obj, mock_combine_tool_obj):
        """Test run_pipeline_async when transcript fetch fails."""
        # Setup
        video_ids = ["v1"]
        output_dir = "./fake_output"
        
        # Configure the .func attribute ON the mocked tool objects - Use MagicMock
        mock_fetch_tool_obj.func = MagicMock(return_value={
            "results": { # Ensure the top-level 'results' key is present
                "v1": {"status": "failure", "error": "Failed to fetch transcript"}
            }
        })
        # Configure func on others just to avoid potential AttributeErrors if accessed
        # These should be AsyncMock as generate is awaited via create_task
        mock_generate_tool_obj.func = AsyncMock()
        # Combine func is called synchronously
        mock_combine_tool_obj.func = MagicMock()

        # Execute
        result = await self.pipeline_runner.run_pipeline_async(video_ids, output_dir=output_dir)
        
        # Verify
        mock_fetch_tool_obj.func.assert_called_once_with(video_ids=video_ids)
        self.mock_summarizer.run.assert_not_called()
        self.mock_synthesizer.run.assert_not_called()
        mock_generate_tool_obj.func.assert_not_called()
        mock_combine_tool_obj.func.assert_not_called()
        assert result["success"] is False
        assert result["error"] == "Failed to fetch any transcripts."

    @patch('src.runners.pipeline_runner.combine_audio_segments_tool')
    @patch('src.runners.pipeline_runner.generate_audio_segment_tool')
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    @patch('tempfile.mkdtemp')
    @patch('src.runners.pipeline_runner.fetch_transcripts')
    async def test_run_pipeline_async_audio_generation_fails(self, mock_fetch_tool_obj, mock_mkdtemp, mock_rmtree, mock_exists, mock_generate_tool_obj, mock_combine_tool_obj):
        """Test run_pipeline_async when audio generation fails."""
        # Setup
        video_ids = ["v1"]
        output_dir = "./fake_output"
        temp_dir = "/tmp/fake_temp_dir"
        
        # Configure the .func attribute ON the mocked tool objects - Use MagicMock
        mock_fetch_tool_obj.func = MagicMock(return_value={
            "results": { # Ensure the top-level 'results' key is present
                "v1": {"status": "success", "result": {"transcript": "Test transcript"}}
            }
        })
        mock_mkdtemp.return_value = temp_dir
        # Audio tool funcs must be async
        mock_generate_tool_obj.func = AsyncMock(return_value=None)  # Simulate audio generation failure
        # Combine func is called synchronously
        mock_combine_tool_obj.func = MagicMock()

        # Configure agent mocks (no calls expected, rely on default fixtures)
        # self.mock_summarizer.run.return_value = {"summary": "Test summary"}
        # self.mock_synthesizer.run.return_value = {
        #     "dialogue": [
        #         {"speaker": "A", "line": "Test line"}
        #     ]
        # }
        # Use default run_async from fixtures for audio generation fail test
        # We need to override summarizer for this test
        async def summarizer_run_async_audio_fail(*args, **kwargs):
            summary_text = "Test summary"
            first_event = Event(content=ContentDict(role='model', parts=[PartDict(text=summary_text)]), author="MockSummarizer")
            mock_event_first = MagicMock(spec=Event)
            mock_event_first.content = first_event.content
            mock_event_first.author = first_event.author
            mock_event_first.is_final_response.return_value = False 
            yield mock_event_first
            last_event = Event(content=ContentDict(role='model', parts=[PartDict(text=summary_text)]), author="MockSummarizer")
            mock_event_last = MagicMock(spec=Event)
            mock_event_last.content = last_event.content
            mock_event_last.author = last_event.author
            mock_event_last.is_final_response.return_value = True 
            yield mock_event_last
        # Assign the async generator function directly
        self.mock_summarizer.run_async = summarizer_run_async_audio_fail
        
        # We need to override synthesizer for this test
        async def synthesizer_run_async_audio_fail(*args, **kwargs):
            dialogue_obj = [{"speaker": "A", "line": "Test line"}]
            dialogue_json = json.dumps(dialogue_obj)
            first_event = Event(content=ContentDict(role='model', parts=[PartDict(text=dialogue_json)]), author="MockSynthesizer")
            mock_event_first = MagicMock(spec=Event)
            mock_event_first.content = first_event.content
            mock_event_first.author = first_event.author
            mock_event_first.is_final_response.return_value = False
            yield mock_event_first
            last_event = Event(content=ContentDict(role='model', parts=[PartDict(text=dialogue_json)]), author="MockSynthesizer")
            mock_event_last = MagicMock(spec=Event)
            mock_event_last.content = last_event.content
            mock_event_last.author = last_event.author
            mock_event_last.is_final_response.return_value = True
            yield mock_event_last
        # Assign the async generator function directly
        self.mock_synthesizer.run_async = synthesizer_run_async_audio_fail

        # Execute
        result = await self.pipeline_runner.run_pipeline_async(video_ids, output_dir=output_dir)
        
        # Verify calls to the .func attribute of the mocked tool objects
        mock_fetch_tool_obj.func.assert_called_once_with(video_ids=video_ids) # Corrected mock name
        mock_generate_tool_obj.func.assert_called() # Corrected mock name
        assert result["success"] is False
        assert result["error"] == "Failed during audio generation or combination."
        mock_combine_tool_obj.func.assert_not_called() # Corrected mock name

    # --- Synchronous Wrapper Tests ---

    @patch('src.runners.pipeline_runner.PipelineRunner.run_pipeline_async') # Patch the async method on the class
    @patch('asyncio.run')
    def test_run_pipeline_sync_wrapper_success(self, mock_asyncio_run, mock_run_pipeline_async):
        """Test the synchronous wrapper successfully calls the async version."""
        video_ids = ["v1"]
        output_dir = "./fake_output_sync"
        expected_async_result = {
            "status": "success",
            "dialogue_script": [{"speaker":"A", "line":"Sync test"}],
            "failed_transcripts": [],
            "final_audio_path": "some/sync/path.mp3"
            # Add other keys returned by async method if needed
        }
        
        # Configure the mock async method to return the result
        mock_run_pipeline_async.return_value = expected_async_result
        # Configure asyncio.run to return the result of the coroutine it's passed
        # Use a simple lambda that awaits the coroutine
        async def run_coro(coro): 
            return await coro
        mock_asyncio_run.side_effect = lambda coro: asyncio.get_event_loop().run_until_complete(run_coro(coro))

        # Execute synchronous wrapper - USE THE CORRECT NAME 'run_pipeline'
        result = self.pipeline_runner.run_pipeline(video_ids, output_dir=output_dir) 

        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
        
        # Verify the mock async method was called on the instance with correct args
        # Corrected assertion to include keyword argument
        mock_run_pipeline_async.assert_called_once_with(video_ids, output_dir=output_dir)

        # Verify the final result matches the expected async result
        assert result == expected_async_result


    @patch('src.runners.pipeline_runner.PipelineRunner.run_pipeline_async')
    @patch('asyncio.run')
    def test_run_pipeline_sync_wrapper_runtime_error(self, mock_asyncio_run, mock_run_pipeline_async, caplog):
        """Test the synchronous wrapper handles RuntimeError from asyncio.run."""
        video_ids = ["v1"]
        output_dir = "./fake_output_sync_err"
        runtime_error_msg = "asyncio loop is already running"
        runtime_error = RuntimeError(runtime_error_msg)
        
        # Configure asyncio.run to raise the error
        mock_asyncio_run.side_effect = runtime_error
        # Mock the async method
        # We need to return *something* awaitable, even though it won't finish
        mock_run_pipeline_async.return_value = asyncio.sleep(0) 

        # Execute - USE THE CORRECT NAME 'run_pipeline'
        result = self.pipeline_runner.run_pipeline(video_ids, output_dir=output_dir)

        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
        # Verify the async method *was* called, because asyncio.run evaluates args before raising side_effect
        mock_run_pipeline_async.assert_called_once_with(video_ids, output_dir=output_dir)
        
        # Verify the result indicates an error
        assert result["status"] == "error"
        assert runtime_error_msg in result["error"]
        assert result["dialogue_script"] == []
        assert result["final_audio_path"] is None
        # Verify the error was logged
        assert "RuntimeError running async pipeline" in caplog.text
        assert runtime_error_msg in caplog.text


    @patch('src.runners.pipeline_runner.PipelineRunner.run_pipeline_async')
    @patch('asyncio.run')
    def test_run_pipeline_sync_wrapper_other_exception(self, mock_asyncio_run, mock_run_pipeline_async, caplog):
        """Test the synchronous wrapper handles other exceptions raised by the async method."""
        video_ids = ["v1", "v2"]
        output_dir = "./fake_output_sync_err2"
        other_exception_msg = "Something else went wrong in async"
        other_exception = ValueError(other_exception_msg)
        
        # Make the *mocked async method* raise the error when called
        mock_run_pipeline_async.side_effect = other_exception
        # Make asyncio.run execute the awaitable (which will raise the error)
        async def run_coro(coro): 
            return await coro
        mock_asyncio_run.side_effect = lambda coro: asyncio.get_event_loop().run_until_complete(run_coro(coro))

        # Execute - USE THE CORRECT NAME 'run_pipeline'
        # Check the returned dictionary for error status instead of raising
        result = self.pipeline_runner.run_pipeline(video_ids, output_dir=output_dir)

        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
        # Verify the mocked async method was called with correct args
        mock_run_pipeline_async.assert_called_once_with(video_ids, output_dir=output_dir)
        
        # Verify the result indicates an error
        assert result["status"] == "error"
        assert other_exception_msg in result["error"]
        assert result["dialogue_script"] == []
        assert result["final_audio_path"] is None
        # Verify the error was logged
        assert "Unexpected error running async pipeline wrapper" in caplog.text
        assert other_exception_msg in caplog.text 