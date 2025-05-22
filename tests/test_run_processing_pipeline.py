import pytest
import asyncio
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock, call

from src.processing.pipeline import run_processing_pipeline
from src.models.api_models import ProcessUrlRequest
from src.core import task_manager

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.fixture
def process_request():
    """Create a sample ProcessUrlRequest object for testing."""
    return ProcessUrlRequest(
        youtube_url="https://www.youtube.com/watch?v=test123",
        summary_length="medium",
        tts_voice="standard_voice_1",
        audio_style="informative"
    )

@pytest.fixture
def task_id():
    """Generate a unique task ID for testing."""
    return str(uuid.uuid4())

@pytest.fixture(autouse=True)
def setup_task_manager():
    """Clear task manager store before and after each test."""
    task_manager._tasks_store.clear()
    yield
    task_manager._tasks_store.clear()

@pytest.mark.asyncio
@patch('src.processing.pipeline.task_manager.update_task_processing_status')
@patch('src.processing.pipeline.task_manager.update_agent_status')
@patch('src.processing.pipeline.task_manager.update_data_flow_status')
@patch('src.processing.pipeline.task_manager.add_agent_log')
async def test_run_processing_pipeline_basic_flow(
    mock_add_log, mock_update_flow, mock_update_agent, mock_update_task,
    task_id, process_request
):
    """Test the basic flow of run_processing_pipeline with all successful steps."""
    
    # Set up a placeholder for synthesizer mock
    with patch('src.processing.pipeline.SynthesizerAgent') as mock_synthesizer_class, \
         patch('src.processing.pipeline.AudioGenerator') as mock_audio_generator_class, \
         patch('asyncio.sleep', return_value=None):  # Skip all sleep calls
        
        # Mock the synthesizer agent
        mock_synth_instance = MagicMock()
        mock_synthesizer_class.return_value = mock_synth_instance
        
        # Mock the run_async method for the synthesizer
        mock_event = AsyncMock()
        mock_event.type = 'RESULT'
        mock_event.payload = {
            'dialogue': [
                {"speaker": "A", "text": "Test line 1"},
                {"speaker": "B", "text": "Test line 2"}
            ]
        }
        
        # Configure the synthesizer run_async to yield a RESULT event
        mock_synth_instance.run_async = AsyncMock()
        mock_synth_instance.run_async.return_value.__aiter__.return_value = [mock_event]
        
        # Mock the audio generator
        mock_audio_instance = MagicMock()
        mock_audio_generator_class.return_value = mock_audio_instance
        mock_audio_instance.run = AsyncMock(return_value={
            "response": "Successfully generated the final audio file at: /path/to/test_output/task_id_digest.mp3"
        })
        
        # Run the pipeline
        await run_processing_pipeline(task_id, process_request)
        
        # Verify the pipeline called update_task_processing_status appropriately
        assert mock_update_task.call_count >= 5  # Initial + YouTube + Transcript + Summarizer + etc.
        
        # Verify agent status updates
        assert mock_update_agent.call_count >= 10  # Multiple updates for each agent
        
        # Verify data flow updates
        assert mock_update_flow.call_count >= 4  # Flows between agents
        
        # Verify logs were added
        assert mock_add_log.call_count >= 4  # Various log entries

@pytest.mark.asyncio
@patch('src.processing.pipeline.task_manager.set_task_failed')
@patch('src.processing.pipeline.task_manager.update_agent_status')
async def test_run_processing_pipeline_error_handling(
    mock_update_agent, mock_set_failed,
    task_id, process_request
):
    """Test that run_processing_pipeline properly handles and logs errors."""
    
    # Force an error during processing
    with patch('src.processing.pipeline.SynthesizerAgent') as mock_synthesizer_class:
        # Make the synthesizer agent throw an exception
        mock_synthesizer_class.side_effect = Exception("Test error in synthesizer")
        
        # Run the pipeline
        await run_processing_pipeline(task_id, process_request)
        
        # Verify task is marked as failed
        mock_set_failed.assert_called_once()
        # The error message should contain our test error
        assert "Test error in synthesizer" in mock_set_failed.call_args[0][1]
        
        # Verify at least one agent was updated with error status
        error_status_calls = [call for call in mock_update_agent.call_args_list 
                             if call[0][2] == "error"]
        assert len(error_status_calls) >= 1

@pytest.mark.asyncio
@patch('src.processing.pipeline.task_manager.set_task_completed')
@patch('src.processing.pipeline.AudioGenerator')
@patch('src.processing.pipeline.SynthesizerAgent')
@patch('asyncio.sleep', return_value=None)  # Skip all sleep calls
async def test_run_processing_pipeline_with_audio_generation(
    mock_sleep, mock_synthesizer_class, mock_audio_generator_class, mock_set_completed,
    task_id, process_request
):
    """Test that run_processing_pipeline correctly generates audio with the AudioGenerator."""
    
    # Mock the synthesizer agent
    mock_synth_instance = MagicMock()
    mock_synthesizer_class.return_value = mock_synth_instance
    
    # Mock the run_async method to yield a result event
    mock_event = MagicMock()
    mock_event.type = 'RESULT'
    mock_event.payload = {
        'dialogue': [
            {"speaker": "A", "text": "Test line 1"},
            {"speaker": "B", "text": "Test line 2"}
        ]
    }
    
    # Configure synthesizer.run_async to yield our mock event
    async def mock_synth_run_async(*args, **kwargs):
        yield mock_event
    
    mock_synth_instance.run_async = mock_synth_run_async
    
    # Mock the audio generator
    mock_audio_instance = MagicMock()
    mock_audio_generator_class.return_value = mock_audio_instance
    
    # Configure audio generator.run to return success
    final_audio_path = f"/output_audio/{task_id}_digest.mp3"
    mock_audio_instance.run = AsyncMock(return_value={
        "response": f"Successfully generated the final audio file at: {final_audio_path}"
    })
    
    # Run the pipeline
    await run_processing_pipeline(task_id, process_request)
    
    # Verify audio generator was called with dialogue script
    mock_audio_instance.run.assert_called_once()
    # Check that the script JSON was passed correctly
    call_arg = mock_audio_instance.run.call_args[0][0]
    assert '"script":' in call_arg
    assert '"speaker": "A"' in call_arg
    assert '"text": "Test line 1"' in call_arg
    
    # Verify task was completed with audio URL
    mock_set_completed.assert_called_once()
    # The third arg should be the audio URL
    audio_url_arg = mock_set_completed.call_args[0][2]
    assert f"/api/v1/audio/{task_id}_digest.mp3" in audio_url_arg or \
           f"audio/{task_id}_digest.mp3" in audio_url_arg

@pytest.mark.asyncio
@patch('src.processing.pipeline.create_test_wav')
@patch('src.processing.pipeline.task_manager.set_task_completed')
@patch('src.processing.pipeline.AudioGenerator')
@patch('src.processing.pipeline.SynthesizerAgent')
@patch('asyncio.sleep', return_value=None)
@patch('src.processing.pipeline.shutil.copy2')  # Mock the new copy function
@patch('subprocess.run')  # Mock the new subprocess call
async def test_run_processing_pipeline_audio_fallback(
    mock_subprocess, mock_copy, mock_sleep, mock_synthesizer_class, 
    mock_audio_generator_class, mock_set_completed, mock_create_test_wav,
    task_id, process_request
):
    """Test that run_processing_pipeline correctly handles audio generation failures."""
    
    # Mock the synthesizer agent
    mock_synth_instance = MagicMock()
    mock_synthesizer_class.return_value = mock_synth_instance
    
    # Mock successful synthesis
    mock_event = MagicMock()
    mock_event.type = 'RESULT'
    mock_event.payload = {
        'dialogue': [
            {"speaker": "A", "text": "Test line 1"},
            {"speaker": "B", "text": "Test line 2"}
        ]
    }
    
    # Configure synthesizer.run_async to yield our mock event
    async def mock_synth_run_async(*args, **kwargs):
        yield mock_event
    
    mock_synth_instance.run_async = mock_synth_run_async
    
    # Mock the audio generator to FAIL
    mock_audio_instance = MagicMock()
    mock_audio_generator_class.return_value = mock_audio_instance
    mock_audio_instance.run = AsyncMock(return_value={
        "error": "Test audio generation failure"
    })
    
    # Ensure the output directory exists
    Path("output_audio").mkdir(exist_ok=True)
    
    # Run the pipeline
    await run_processing_pipeline(task_id, process_request)
    
    # Verify audio generator was called
    mock_audio_instance.run.assert_called_once()
    
    # Verify fallback audio was created - our new implementation tries MP3 conversion
    assert mock_create_test_wav.called
    
    # Verify task was still completed (with fallback audio URL)
    mock_set_completed.assert_called_once()
    # The third arg should be the audio URL
    audio_url_arg = mock_set_completed.call_args[0][2]
    assert f"/api/v1/audio/{task_id}_digest.mp3" in audio_url_arg or \
           f"audio/{task_id}_digest.mp3" in audio_url_arg