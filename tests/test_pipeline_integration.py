import pytest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import json
import tempfile
import shutil

# Add project root to sys.path to allow importing src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.runners.pipeline_runner import PipelineRunner
from src.agents.transcript_fetcher import TranscriptFetcher
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.audio_generator import AudioGenerator
from src.core import task_manager
from src.models.api_models import TaskStatusResponse, ProcessingStatus, AgentNode
from src.agents.base_agent import BaseAgentEvent, BaseAgentEventType

# --- Fixtures ---

@pytest.fixture
def mock_agents():
    """Create mock instances of all required agents."""
    transcript_fetcher = MagicMock(spec=TranscriptFetcher)
    summarizer = MagicMock(spec=SummarizerAgent)
    synthesizer = MagicMock(spec=SynthesizerAgent)
    audio_generator = MagicMock(spec=AudioGenerator)
    
    # Set names for easier identification in logs
    transcript_fetcher.name = "MockTranscriptFetcher"
    summarizer.name = "MockSummarizer"
    synthesizer.name = "MockSynthesizer"
    audio_generator.name = "MockAudioGenerator"
    
    return {
        "transcript_fetcher": transcript_fetcher,
        "summarizer": summarizer,
        "synthesizer": synthesizer,
        "audio_generator": audio_generator
    }

@pytest.fixture
def pipeline_runner(mock_agents):
    """Create a PipelineRunner with mock agents."""
    return PipelineRunner(
        transcript_fetcher=mock_agents["transcript_fetcher"],
        summarizer=mock_agents["summarizer"],
        synthesizer=mock_agents["synthesizer"],
        audio_generator=mock_agents["audio_generator"]
    )

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files and clean it up after tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

# --- Mock BaseAgentEvent Creator Helper ---

def create_mock_agent_event(event_type, payload=None):
    """Create a mock BaseAgentEvent with the specified type and payload."""
    if payload is None:
        payload = {}
    return BaseAgentEvent(type=event_type, payload=payload)

# --- Tests ---

class TestPipelineIntegration:
    """Test the integration of the PipelineRunner with task_manager and agents."""
    
    @pytest.mark.asyncio
    @patch('src.core.task_manager.update_agent_status')
    @patch('src.core.task_manager.update_task_processing_status')
    @patch('src.core.task_manager.add_timeline_event')
    @patch('src.tools.transcript_tools.fetch_transcripts')
    async def test_pipeline_updates_task_status_during_execution(
        self, mock_fetch, mock_add_timeline, mock_update_task, mock_update_agent, 
        pipeline_runner, mock_agents, temp_output_dir
    ):
        """Test that the pipeline updates task status through task_manager during execution."""
        # Setup
        video_ids = ["video123"]
        task_id = "test-task-123"
        
        # Mock fetch_transcripts to return success with the expected structure
        mock_fetch.return_value = {
            "results": {  # Note the results key in the top level
                "video123": {
                    "status": "success",
                    "result": {"transcript": "Test transcript content"},
                    "error": None
                }
            }
        }
        
        # Setup agent mocks to yield progress and result events
        async def mock_summarizer_run_async(input_data):
            # First yield a progress event
            yield create_mock_agent_event(
                BaseAgentEventType.PROGRESS, 
                {"progress": 50, "message": "Summarizing in progress"}
            )
            # Then yield a result event
            yield create_mock_agent_event(
                BaseAgentEventType.RESULT,
                {"summary": "This is a summary of the test transcript."}
            )
        
        async def mock_synthesizer_run_async(input_data):
            # First yield a progress event
            yield create_mock_agent_event(
                BaseAgentEventType.PROGRESS, 
                {"progress": 50, "message": "Synthesizing in progress"}
            )
            # Then yield a result event
            dialogue = [
                {"speaker": "A", "text": "Welcome to the podcast."},
                {"speaker": "B", "text": "Thank you for having me."}
            ]
            yield create_mock_agent_event(
                BaseAgentEventType.RESULT,
                {"dialogue": dialogue}
            )
        
        # Setup audio generator mock
        async def mock_audio_generator_run_async(input_data):
            # Yield a progress event
            yield create_mock_agent_event(
                BaseAgentEventType.PROGRESS, 
                {"progress": 50, "message": "Generating audio in progress"}
            )
            # Then yield a result event
            final_audio_path = os.path.join(temp_output_dir, "final_audio.mp3")
            yield create_mock_agent_event(
                BaseAgentEventType.RESULT,
                {"audio_path": final_audio_path}
            )
        
        # Assign the async generators to the mocks
        mock_agents["summarizer"].run_async = mock_summarizer_run_async
        mock_agents["synthesizer"].run_async = mock_synthesizer_run_async
        mock_agents["audio_generator"].run_async = mock_audio_generator_run_async
        
        # Run the pipeline with a task_id parameter (might need to modify pipeline_runner.run_pipeline_async)
        with patch.object(pipeline_runner, '_run_agent_get_final_response', wraps=pipeline_runner._run_agent_get_final_response) as mock_run_agent:
            # Add the task_id parameter to the function call if supported
            try:
                result = await pipeline_runner.run_pipeline_async(video_ids, temp_output_dir, task_id=task_id)
            except TypeError:
                # If task_id parameter isn't supported, use context patching instead
                with patch('src.core.task_manager._current_task_id', task_id):
                    result = await pipeline_runner.run_pipeline_async(video_ids, temp_output_dir)
        
        # Verify task_manager interactions
        # Verify updates to overall task status
        assert mock_update_task.call_count >= 2, "Should update task status at least twice (start and completion)"
        # Verify updates to individual agent statuses
        assert mock_update_agent.call_count >= 3, "Should update agent status for each agent in the pipeline"
        # Verify timeline events were added
        assert mock_add_timeline.call_count >= 3, "Should add timeline events for key pipeline steps"
        
        # Verify _run_agent_get_final_response was called for each agent
        assert mock_run_agent.call_count >= 3, "Should call _run_agent_get_final_response for each agent"
        
        # Verify result contains expected keys (based on updated return structure)
        assert "success" in result
        assert result["success"] is True
        # Check for final_audio_path instead of audio_path in the updated implementation
        assert "final_audio_path" in result
    
    @pytest.mark.asyncio
    async def test_pipeline_handles_agent_errors_gracefully(
        self, pipeline_runner, mock_agents, temp_output_dir
    ):
        """Test that the pipeline handles errors from agents gracefully and reports them properly."""
        # Setup
        video_ids = ["video123"]
        
        # Mock fetch_transcripts to return success with the updated structure
        with patch('src.tools.transcript_tools.fetch_transcripts') as mock_fetch:
            mock_fetch.return_value = {
                "results": {  # Note the results key in the top level
                    "video123": {
                        "status": "success",
                        "result": {"transcript": "Test transcript content"},
                        "error": None
                    }
                }
            }
            
            # Make the summarizer agent fail with an error event
            async def mock_summarizer_error_async(input_data):
                yield create_mock_agent_event(
                    BaseAgentEventType.ERROR,
                    {"error": "Summarization failed due to content analysis error."}
                )
            
            mock_agents["summarizer"].run_async = mock_summarizer_error_async
            
            # Run the pipeline
            result = await pipeline_runner.run_pipeline_async(video_ids, temp_output_dir)
            
            # Verify the result indicates failure
            assert "success" in result
            assert result["success"] is False
            assert "error" in result
            assert "Summarization failed" in result["error"]
    
    @pytest.mark.asyncio
    @patch('src.core.task_manager.update_agent_status')
    @patch('src.core.task_manager.update_data_flow_status')
    async def test_pipeline_data_flow_tracking(
        self, mock_update_flow, mock_update_agent, 
        pipeline_runner, mock_agents, temp_output_dir
    ):
        """Test that the pipeline tracks data flow between agents."""
        # Setup
        video_ids = ["video123"]
        
        # Mock fetch_transcripts to return success with the updated structure
        with patch('src.tools.transcript_tools.fetch_transcripts') as mock_fetch:
            mock_fetch.return_value = {
                "results": {  # Note the results key in the top level
                    "video123": {
                        "status": "success",
                        "result": {"transcript": "Test transcript content"},
                        "error": None
                    }
                }
            }
            
            # Setup successful agent mocks that match the expected response formats
            # For summarizer agent
            async def mock_summarizer_success(input_data):
                yield create_mock_agent_event(
                    BaseAgentEventType.RESULT,
                    {"summary": "This is a test summary"}
                )
            
            # For synthesizer agent
            async def mock_synthesizer_success(input_data):
                dialogue = [
                    {"speaker": "A", "text": "Welcome to the podcast."},
                    {"speaker": "B", "text": "Thank you for having me."}
                ]
                yield create_mock_agent_event(
                    BaseAgentEventType.RESULT,
                    {"dialogue": dialogue}
                )
            
            # For audio generator
            async def mock_audio_generator_success(input_data):
                final_audio_path = os.path.join(temp_output_dir, "final_audio.mp3")
                yield create_mock_agent_event(
                    BaseAgentEventType.RESULT,
                    {"audio_path": final_audio_path}
                )
            
            # Assign the mock implementations
            mock_agents["summarizer"].run_async = mock_summarizer_success
            mock_agents["synthesizer"].run_async = mock_synthesizer_success
            mock_agents["audio_generator"].run_async = mock_audio_generator_success
            
            # Run the pipeline
            await pipeline_runner.run_pipeline_async(video_ids, temp_output_dir)
            
            # Verify data flow updates
            # Note: This assumes the pipeline calls update_data_flow_status for each data flow
            assert mock_update_flow.call_count >= 3, "Should update data flow status for each transition between agents"
    
    @pytest.mark.asyncio
    async def test_pipeline_cleanup_on_success(self, pipeline_runner, mock_agents, temp_output_dir):
        """Test that the pipeline cleans up temporary resources on successful completion."""
        # Setup
        video_ids = ["video123"]
        
        # Mock fetch_transcripts to return success
        with patch('src.tools.transcript_tools.fetch_transcripts') as mock_fetch:
            mock_fetch.return_value = {
                "video123": {
                    "success": True,
                    "transcript": "Test transcript content",
                    "error": None
                }
            }
            
            # Setup successful agent mocks
            async def mock_successful_agent_run(input_data):
                yield create_mock_agent_event(
                    BaseAgentEventType.RESULT,
                    {"result": "Agent completed successfully"}
                )
            
            mock_agents["summarizer"].run_async = mock_successful_agent_run
            mock_agents["synthesizer"].run_async = mock_successful_agent_run
            mock_agents["audio_generator"].run_async = mock_successful_agent_run
            
            # Mock tempfile.mkdtemp to track temp dirs
            temp_dirs = []
            original_mkdtemp = tempfile.mkdtemp
            
            def mock_mkdtemp(*args, **kwargs):
                temp_dir = original_mkdtemp(*args, **kwargs)
                temp_dirs.append(temp_dir)
                return temp_dir
            
            with patch('tempfile.mkdtemp', side_effect=mock_mkdtemp), \
                 patch('shutil.rmtree') as mock_rmtree:
                
                # Run the pipeline
                await pipeline_runner.run_pipeline_async(video_ids, temp_output_dir)
                
                # Verify cleanup was called for each temp dir
                for temp_dir in temp_dirs:
                    mock_rmtree.assert_any_call(temp_dir)
    
    @pytest.mark.asyncio
    async def test_pipeline_cleanup_on_error(self, pipeline_runner, mock_agents, temp_output_dir):
        """Test that the pipeline cleans up temporary resources even when errors occur."""
        # Setup
        video_ids = ["video123"]
        
        # Mock fetch_transcripts to return success
        with patch('src.tools.transcript_tools.fetch_transcripts') as mock_fetch:
            mock_fetch.return_value = {
                "video123": {
                    "success": True,
                    "transcript": "Test transcript content",
                    "error": None
                }
            }
            
            # Make the summarizer agent fail with an error event
            async def mock_summarizer_error_async(input_data):
                yield create_mock_agent_event(
                    BaseAgentEventType.ERROR,
                    {"error": "Summarization failed due to content analysis error."}
                )
            
            mock_agents["summarizer"].run_async = mock_summarizer_error_async
            
            # Mock tempfile.mkdtemp to track temp dirs
            temp_dirs = []
            original_mkdtemp = tempfile.mkdtemp
            
            def mock_mkdtemp(*args, **kwargs):
                temp_dir = original_mkdtemp(*args, **kwargs)
                temp_dirs.append(temp_dir)
                return temp_dir
            
            with patch('tempfile.mkdtemp', side_effect=mock_mkdtemp), \
                 patch('shutil.rmtree') as mock_rmtree:
                
                # Run the pipeline
                await pipeline_runner.run_pipeline_async(video_ids, temp_output_dir)
                
                # Verify cleanup was called for each temp dir
                for temp_dir in temp_dirs:
                    mock_rmtree.assert_any_call(temp_dir)
    
    @pytest.mark.asyncio
    @patch('src.core.task_manager.get_task_status')
    @patch('src.core.task_manager.update_task_processing_status')
    async def test_pipeline_estimated_completion_time(
        self, mock_update_task, mock_get_task, pipeline_runner, mock_agents, temp_output_dir
    ):
        """Test that the pipeline provides and updates estimated completion time."""
        # Setup
        video_ids = ["video123"]
        task_id = "test-task-estimated-time"
        
        # Mock task status
        mock_task_status = TaskStatusResponse(
            task_id=task_id,
            processing_status=ProcessingStatus(
                status="processing",
                overall_progress=0,
                start_time="2023-01-01T12:00:00Z"
            ),
            agents=[
                AgentNode(
                    id="transcript-fetcher",
                    name="Transcript Fetcher",
                    description="Fetches video transcript.",
                    type="transcription",
                    status="pending",
                    icon="FileText",
                    progress=0
                )
            ],
            data_flows=[],
            timeline=[]
        )
        mock_get_task.return_value = mock_task_status
        
        # Mock fetch_transcripts to return success
        with patch('src.tools.transcript_tools.fetch_transcripts') as mock_fetch:
            mock_fetch.return_value = {
                "video123": {
                    "success": True,
                    "transcript": "Test transcript content",
                    "error": None
                }
            }
            
            # Setup successful agent mocks with delays to simulate processing time
            async def mock_agent_with_progress(input_data):
                # Yield progress events
                for progress in [25, 50, 75]:
                    yield create_mock_agent_event(
                        BaseAgentEventType.PROGRESS,
                        {"progress": progress, "message": f"Processing at {progress}%"}
                    )
                    await asyncio.sleep(0.1)  # Small delay to simulate work
                
                # Yield final result
                yield create_mock_agent_event(
                    BaseAgentEventType.RESULT,
                    {"result": "Agent completed successfully"}
                )
            
            mock_agents["summarizer"].run_async = mock_agent_with_progress
            mock_agents["synthesizer"].run_async = mock_agent_with_progress
            mock_agents["audio_generator"].run_async = mock_agent_with_progress
            
            # Run the pipeline with task_id
            with patch.object(task_manager, '_tasks_store', {task_id: mock_task_status}):
                try:
                    await pipeline_runner.run_pipeline_async(video_ids, temp_output_dir, task_id=task_id)
                except TypeError:
                    # If task_id parameter isn't supported, use context patching
                    with patch('src.core.task_manager._current_task_id', task_id):
                        await pipeline_runner.run_pipeline_async(video_ids, temp_output_dir)
            
            # Verify estimated_end_time was updated
            # Find calls to update_task_processing_status that include estimated_end_time
            estimated_time_updates = 0
            for call_args in mock_update_task.call_args_list:
                args, kwargs = call_args
                if len(args) >= 3 and args[0] == task_id:  # First arg is task_id
                    if kwargs.get('estimated_end_time') or (len(args) > 3 and args[3]):
                        estimated_time_updates += 1
            
            assert estimated_time_updates > 0, "Should update estimated completion time at least once" 