import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Use absolute paths for imports from src
from src.runners.pipeline_runner import PipelineRunner
from src.agents.transcript_fetcher import TranscriptFetcher
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.audio_generator import AudioGenerator
from src.tools.transcript_tools import fetch_transcripts

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

# --- Test Fixtures ---

@pytest.fixture
def mock_transcript_fetcher():
    """Fixture for a mock TranscriptFetcher agent."""
    return MagicMock(spec=TranscriptFetcher)

@pytest.fixture
def mock_summarizer():
    """Fixture for a mock SummarizerAgent."""
    return MagicMock(spec=SummarizerAgent)

@pytest.fixture
def mock_synthesizer():
    """Fixture for a mock SynthesizerAgent."""
    return MagicMock(spec=SynthesizerAgent)

@pytest.fixture
def mock_audio_generator():
    """Fixture for a mock AudioGenerator agent."""
    return MagicMock(spec=AudioGenerator)

@pytest.fixture
def pipeline_runner(mock_transcript_fetcher, mock_summarizer, mock_synthesizer, mock_audio_generator):
    """Fixture for a PipelineRunner instance with mock agents."""
    return PipelineRunner(
        transcript_fetcher=mock_transcript_fetcher,
        summarizer=mock_summarizer,
        synthesizer=mock_synthesizer,
        audio_generator=mock_audio_generator
    )

# --- Test Cases ---

def test_pipeline_runner_initialization(pipeline_runner, mock_transcript_fetcher, mock_summarizer, mock_synthesizer, mock_audio_generator):
    """Test that PipelineRunner initializes correctly with agents."""
    assert pipeline_runner.transcript_fetcher is mock_transcript_fetcher
    assert pipeline_runner.summarizer is mock_summarizer
    assert pipeline_runner.synthesizer is mock_synthesizer
    assert pipeline_runner.audio_generator is mock_audio_generator

@pytest.mark.parametrize(
    "input_results, expected_transcripts, expected_failures",
    [
        # Happy path: all success
        (
            {"v1": {"status": "success", "result": {"transcript": "text1"}}, "v2": {"status": "success", "result": {"transcript": "text2"}}},
            {"v1": "text1", "v2": "text2"},
            []
        ),
        # Partial failure
        (
            {"v1": {"status": "success", "result": {"transcript": "text1"}}, "v2": {"status": "error", "error": "Fetch failed"}, "v3": {"status": "success", "result": {"transcript": ""}}},
            {"v1": "text1", "v3": ""},
            ["v2"]
        ),
        # All failures
        (
            {"v1": {"status": "error", "error": "Bad ID"}, "v2": {"status": "error", "error": "Private video"}},
            {},
            ["v1", "v2"]
        ),
        # Empty input
        (
            {},
            {},
            []
        ),
        # Input with missing keys (should handle gracefully)
        (
            {"v1": {"status": "success"}, "v2": {"status": "success", "result": {}}}, # Missing 'result'/'transcript'
            {"v1": "", "v2": ""},
            []
        )
    ]
)
def test_process_transcript_results(pipeline_runner, input_results, expected_transcripts, expected_failures):
    """Test the _process_transcript_results helper method."""
    transcripts, failed_fetches = pipeline_runner._process_transcript_results(input_results)
    assert transcripts == expected_transcripts
    assert sorted(failed_fetches) == sorted(expected_failures)

# --- Async Pipeline Tests ---

# Patch the tool functions where they are used in the runner module
@patch('src.runners.pipeline_runner.shutil.rmtree')
@patch('src.runners.pipeline_runner.tempfile.mkdtemp')
@patch('src.runners.pipeline_runner.combine_audio_segments_tool.func')
@patch('src.runners.pipeline_runner.generate_audio_segment_tool.func')
@patch('src.runners.pipeline_runner.fetch_transcripts.func')
async def test_run_pipeline_async_happy_path(
    mock_fetch_func, 
    mock_generate_func, 
    mock_combine_func, 
    mock_mkdtemp, 
    mock_rmtree, 
    pipeline_runner
):
    """Test run_pipeline_async with successful transcript fetch and simulated steps including audio."""
    video_ids = ["v1", "v2"]
    output_dir = "./fake_output"
    temp_dir = "/tmp/fake_temp_dir_123"
    final_audio = f"{output_dir}/podcast_digest_mock_timestamp.mp3"

    # --- Mock Configuration ---
    mock_mkdtemp.return_value = temp_dir
    # Simulate successful transcript fetch
    mock_fetch_func.return_value = {
        "results": {
            "v1": {"status": "success", "result": {"transcript": "Transcript 1 text."}},
            "v2": {"status": "success", "result": {"transcript": "Transcript 2 text."}}
        }
    }
    # Simulate successful segment generation (return the path it was asked to write to)
    mock_generate_func.side_effect = lambda text, speaker, output_filepath, tts_client: output_filepath
    # Simulate successful combination
    mock_combine_func.return_value = final_audio

    # --- Run Test ---
    result = await pipeline_runner.run_pipeline_async(video_ids, output_dir=output_dir)

    # --- Assertions ---
    # Transcript fetch
    mock_fetch_func.assert_called_once_with(video_ids=video_ids)
    # Temp directory creation
    mock_mkdtemp.assert_called_once()
    # Audio segment generation (called twice, once for each dialogue line)
    assert mock_generate_func.call_count == 2
    mock_generate_func.assert_any_call(
        text="Hello, this is a simulated dialogue based on summaries.", 
        speaker="A", 
        output_filepath=f"{temp_dir}/segment_000_A.mp3",
        tts_client=unittest.mock.ANY # Check tts_client was passed
    )
    mock_generate_func.assert_any_call(
        text="Indeed, covering 2 points.", 
        speaker="B", 
        output_filepath=f"{temp_dir}/segment_001_B.mp3",
        tts_client=unittest.mock.ANY
    )
    # Audio combination
    expected_segment_paths = [f"{temp_dir}/segment_000_A.mp3", f"{temp_dir}/segment_001_B.mp3"]
    mock_combine_func.assert_called_once_with(segment_filepaths=expected_segment_paths, output_dir=output_dir)
    # Temp directory cleanup
    mock_rmtree.assert_called_once_with(temp_dir)
    # Result dictionary
    assert result["status"] == "success"
    assert result["failed_transcripts"] == []
    assert result["summary_count"] == 2 # Based on simulation
    assert isinstance(result["dialogue_script"], list)
    assert len(result["dialogue_script"]) == 2
    assert result["final_audio_path"] == final_audio


@patch('src.runners.pipeline_runner.shutil.rmtree')
@patch('src.runners.pipeline_runner.tempfile.mkdtemp')
@patch('src.runners.pipeline_runner.combine_audio_segments_tool.func')
@patch('src.runners.pipeline_runner.generate_audio_segment_tool.func')
@patch('src.runners.pipeline_runner.fetch_transcripts.func')
async def test_run_pipeline_async_segment_generation_fails(
    mock_fetch_func, 
    mock_generate_func, 
    mock_combine_func, 
    mock_mkdtemp, 
    mock_rmtree, 
    pipeline_runner
):
    """Test run_pipeline_async when one audio segment fails to generate."""
    video_ids = ["v1"]
    output_dir = "./fake_output"
    temp_dir = "/tmp/fake_temp_dir_456"
    final_audio = f"{output_dir}/podcast_digest_mock_timestamp.mp3"
    
    mock_mkdtemp.return_value = temp_dir
    mock_fetch_func.return_value = {"results": {"v1": {"status": "success", "result": {"transcript": "T1"}}}}
    # Simulate one success, one failure for generate
    mock_generate_func.side_effect = [f"{temp_dir}/segment_000_A.mp3", None] 
    mock_combine_func.return_value = final_audio # Simulates combination of only the first segment

    result = await pipeline_runner.run_pipeline_async(video_ids, output_dir=output_dir)

    mock_mkdtemp.assert_called_once()
    assert mock_generate_func.call_count == 2 # Still attempted both
    # Combine should be called only with the successful segment
    mock_combine_func.assert_called_once_with(segment_filepaths=[f"{temp_dir}/segment_000_A.mp3"], output_dir=output_dir)
    mock_rmtree.assert_called_once_with(temp_dir)
    # Status is success because concatenation still produced a file
    assert result["status"] == "success" 
    assert result["final_audio_path"] == final_audio
    assert len(result["dialogue_script"]) == 2 # Dialogue still generated


@patch('src.runners.pipeline_runner.shutil.rmtree')
@patch('src.runners.pipeline_runner.tempfile.mkdtemp')
@patch('src.runners.pipeline_runner.combine_audio_segments_tool.func')
@patch('src.runners.pipeline_runner.generate_audio_segment_tool.func')
@patch('src.runners.pipeline_runner.fetch_transcripts.func')
async def test_run_pipeline_async_combination_fails(
    mock_fetch_func, 
    mock_generate_func, 
    mock_combine_func, 
    mock_mkdtemp, 
    mock_rmtree, 
    pipeline_runner
):
    """Test run_pipeline_async when audio combination fails."""
    video_ids = ["v1"]
    output_dir = "./fake_output"
    temp_dir = "/tmp/fake_temp_dir_789"
    
    mock_mkdtemp.return_value = temp_dir
    mock_fetch_func.return_value = {"results": {"v1": {"status": "success", "result": {"transcript": "T1"}}}}
    mock_generate_func.side_effect = lambda text, speaker, output_filepath, tts_client: output_filepath
    mock_combine_func.return_value = None # Simulate combination failure

    result = await pipeline_runner.run_pipeline_async(video_ids, output_dir=output_dir)

    mock_mkdtemp.assert_called_once()
    assert mock_generate_func.call_count == 2
    mock_combine_func.assert_called_once() # Combination was attempted
    mock_rmtree.assert_called_once_with(temp_dir)
    assert result["status"] == "partial_failure" # Status reflects combination failure
    assert result["final_audio_path"] is None
    assert len(result["dialogue_script"]) == 2


@patch('src.runners.pipeline_runner.shutil.rmtree')
@patch('src.runners.pipeline_runner.tempfile.mkdtemp')
@patch('src.runners.pipeline_runner.combine_audio_segments_tool.func')
@patch('src.runners.pipeline_runner.generate_audio_segment_tool.func')
@patch('src.runners.pipeline_runner.fetch_transcripts.func')
async def test_run_pipeline_async_no_dialogue(
    mock_fetch_func, 
    mock_generate_func, 
    mock_combine_func, 
    mock_mkdtemp, 
    mock_rmtree, 
    pipeline_runner
):
    """Test run_pipeline_async when no dialogue script is generated (e.g., no summaries)."""
    video_ids = ["v1"]
    output_dir = "./fake_output"

    # Simulate successful transcript fetch but no summaries/dialogue later
    mock_fetch_func.return_value = {"results": {"v1": {"status": "success", "result": {"transcript": ""}}}} # Empty transcript -> no summary -> no dialogue

    # Need to modify runner's internal simulation for this test
    # Easier approach: Mock the dialogue_script result directly within the test scope if runner logic complex
    # For now, assume the existing simulation logic correctly produces empty dialogue_script

    result = await pipeline_runner.run_pipeline_async(video_ids, output_dir=output_dir)

    mock_mkdtemp.assert_not_called() # No temp dir needed
    mock_generate_func.assert_not_called() # No segments generated
    mock_combine_func.assert_not_called() # No combination attempted
    mock_rmtree.assert_not_called() # No temp dir to clean
    assert result["status"] == "partial_failure" # No audio generated
    assert result["dialogue_script"] == []
    assert result["final_audio_path"] is None


# --- Sync Wrapper Tests --- 

# NOTE: We patch the runner *instance's* async method here, not the class method directly
# And we patch asyncio.run from the context *where it's called* (pipeline_runner module)

@patch('src.runners.pipeline_runner.asyncio.run')
def test_run_pipeline_sync_wrapper_success(mock_asyncio_run, pipeline_runner):
    """Test the synchronous run_pipeline wrapper calling the async version."""
    video_ids = ["v1"]
    output_dir = "./fake_output_sync"
    expected_async_result = {
        "status": "success", 
        "dialogue_script": [{"speaker":"A", "line":"done"}], 
        "failed_transcripts": [], 
        "summary_count": 1,
        "final_audio_path": f"{output_dir}/final.mp3"
    }

    # Mock the instance's async method directly
    pipeline_runner.run_pipeline_async = AsyncMock(return_value=expected_async_result)

    # Configure asyncio.run to return the result of calling the (now mocked) async func
    mock_asyncio_run.return_value = expected_async_result

    # Call the sync wrapper, passing the output_dir
    sync_result = pipeline_runner.run_pipeline(video_ids, output_dir=output_dir)

    # Check that asyncio.run was called with the instance's async method and args
    mock_asyncio_run.assert_called_once()
    # Check the coroutine object passed to asyncio.run
    args, kwargs = mock_asyncio_run.call_args
    coro = args[0]
    assert coro.cr_code.co_name == 'run_pipeline_async' # Check it's the right coroutine
    # Check the call to the mocked async method
    pipeline_runner.run_pipeline_async.assert_called_once_with(video_ids, output_dir=output_dir)

    assert sync_result == expected_async_result

@patch('src.runners.pipeline_runner.asyncio.run')
def test_run_pipeline_sync_wrapper_runtime_error(mock_asyncio_run, pipeline_runner):
    """Test the synchronous wrapper handles RuntimeError from asyncio.run."""
    video_ids = ["v1"]
    output_dir = "./fake_output_sync_err"
    runtime_error = RuntimeError("asyncio loop is already running")
    mock_asyncio_run.side_effect = runtime_error

    # Mock the instance's async method (though it won't be successfully awaited)
    pipeline_runner.run_pipeline_async = AsyncMock()

    sync_result = pipeline_runner.run_pipeline(video_ids, output_dir=output_dir)

    mock_asyncio_run.assert_called_once()
    # Check that run_pipeline_async was still *prepared* to be called by asyncio.run
    args, kwargs = mock_asyncio_run.call_args
    coro = args[0]
    assert coro.cr_code.co_name == 'run_pipeline_async'
    
    assert sync_result == {
        "status": "error",
        "error": str(runtime_error),
        "dialogue_script": [],
        "failed_transcripts": video_ids,
        "summary_count": 0,
        "final_audio_path": None # Added check
    }

@patch('src.runners.pipeline_runner.asyncio.run')
def test_run_pipeline_sync_wrapper_other_exception(mock_asyncio_run, pipeline_runner):
    """Test the synchronous wrapper handles other exceptions during async run."""
    video_ids = ["v1", "v2"]
    output_dir = "./fake_output_sync_err2"
    other_exception = ValueError("Something else went wrong")
    mock_asyncio_run.side_effect = other_exception

    # Mock the instance's async method
    pipeline_runner.run_pipeline_async = AsyncMock()

    sync_result = pipeline_runner.run_pipeline(video_ids, output_dir=output_dir)

    mock_asyncio_run.assert_called_once()
     # Check that run_pipeline_async was still *prepared* to be called by asyncio.run
    args, kwargs = mock_asyncio_run.call_args
    coro = args[0]
    assert coro.cr_code.co_name == 'run_pipeline_async'

    assert sync_result == {
        "status": "error",
        "error": str(other_exception),
        "dialogue_script": [],
        "failed_transcripts": video_ids,
        "summary_count": 0,
        "final_audio_path": None # Added check
    } 