import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import os

from src.agents.audio_generator import AudioGenerator
from src.tools.audio_tools import generate_audio_segment_tool, combine_audio_segments_tool

@pytest.fixture
def agent():
    """Creates an AudioGenerator agent for testing."""
    return AudioGenerator()

@pytest.mark.asyncio
async def test_agent_initialization(agent):
    """Test that the agent initializes with the correct parameters."""
    assert agent.name == "AudioGenerator"
    assert "audio processing agent" in agent.instruction.lower()
    assert len(agent.tools) == 2
    assert generate_audio_segment_tool in agent.tools
    assert combine_audio_segments_tool in agent.tools

@pytest.mark.asyncio
async def test_agent_run_with_valid_script():
    """Test that the agent can successfully generate audio from a valid script."""
    agent = AudioGenerator()
    
    # Create a sample dialogue script
    dialogue_script = [
        {"speaker": "A", "text": "Hello, welcome to our podcast."},
        {"speaker": "B", "text": "Thank you for having me."}
    ]
    
    # Mock paths for generated segments and final output
    segment_paths = [
        "/tmp/segment_1.mp3",
        "/tmp/segment_2.mp3"
    ]
    final_output_path = "/output/podcast_digest_20230101_120000.mp3"
    
    # Mock the generate_audio_segment_tool.run method
    async def mock_generate_segment(*args, **kwargs):
        # Return the appropriate segment path based on call count
        call_count = mock_generate.call_count
        return segment_paths[call_count - 1]
    
    mock_generate = AsyncMock(side_effect=mock_generate_segment)
    
    # Mock the combine_audio_segments_tool.run method
    mock_combine = AsyncMock(return_value=final_output_path)
    
    with patch.object(generate_audio_segment_tool, 'run', mock_generate), \
         patch.object(combine_audio_segments_tool, 'run', mock_combine):
        
        # Mock the LLM response
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
            mock_response = AsyncMock()
            mock_response.text = f"""
            I'll process the dialogue script to generate audio:
            
            1. First, I'll generate audio for each line in the script:
            
            For speaker A: "Hello, welcome to our podcast."
            Using generate_audio_segment tool... Saved to {segment_paths[0]}
            
            For speaker B: "Thank you for having me."
            Using generate_audio_segment tool... Saved to {segment_paths[1]}
            
            2. Now I'll combine all segments into one file:
            Using combine_audio_segments tool... 
            
            Successfully generated the final audio file at: {final_output_path}
            """
            mock_generate_content.return_value = mock_response
            
            # Create input data for the agent
            input_data = {
                "script": dialogue_script,
                "output_dir": "/output"
            }
            
            # Run the agent
            result = await agent.run(json.dumps(input_data))
            
            # Verify the agent returned the expected response
            assert "response" in result
            assert final_output_path in result["response"]
            
            # Verify the generate_segment tool was called twice
            assert mock_generate.call_count == 2
            
            # Verify the combine_segments tool was called once with the segment paths
            mock_combine.assert_called_once()
            # The first argument of the first call
            args, _ = mock_combine.call_args
            assert args[0] == segment_paths

@pytest.mark.asyncio
async def test_agent_run_with_empty_script():
    """Test that the agent handles an empty script gracefully."""
    agent = AudioGenerator()
    
    # Create an empty dialogue script
    dialogue_script = []
    
    # Mock the LLM response
    with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
        mock_response = AsyncMock()
        mock_response.text = "I can't generate audio from an empty script. Please provide a valid dialogue script with speaker and text entries."
        mock_generate_content.return_value = mock_response
        
        # Create input data for the agent
        input_data = {
            "script": dialogue_script,
            "output_dir": "/output"
        }
        
        # Run the agent
        result = await agent.run(json.dumps(input_data))
        
        # Verify the agent returned an appropriate error message
        assert "response" in result
        assert "empty script" in result["response"].lower()
        
        # Verify the functions were called
        mock_generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_agent_run_with_invalid_input_format():
    """Test that the agent handles invalid input format gracefully."""
    agent = AudioGenerator()
    
    # Invalid input (not a properly formatted dialogue script)
    invalid_input = "This is not a valid JSON string"
    
    # Mock the LLM response
    with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
        mock_response = AsyncMock()
        mock_response.text = "The input is not valid. Please provide a properly formatted JSON string with 'script' and 'output_dir' fields."
        mock_generate_content.return_value = mock_response
        
        # Run the agent
        result = await agent.run(invalid_input)
        
        # Verify the agent returned an appropriate error message
        assert "response" in result
        assert "not valid" in result["response"].lower()
        
        # Verify the functions were called
        mock_generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_agent_handles_segment_generation_error():
    """Test that the agent handles errors during segment generation."""
    agent = AudioGenerator()
    
    # Create a sample dialogue script
    dialogue_script = [
        {"speaker": "A", "text": "Hello, welcome to our podcast."},
        {"speaker": "B", "text": "Thank you for having me."}
    ]
    
    # Mock the generate_audio_segment_tool.run method to return None (indicating failure)
    mock_generate = AsyncMock(return_value=None)
    
    with patch.object(generate_audio_segment_tool, 'run', mock_generate):
        
        # Mock the LLM response
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
            mock_response = AsyncMock()
            mock_response.text = """
            I encountered an error while generating audio for the first segment.
            The generate_audio_segment tool returned None, indicating a failure.
            Please check your TTS service configuration and try again.
            """
            mock_generate_content.return_value = mock_response
            
            # Create input data for the agent
            input_data = {
                "script": dialogue_script,
                "output_dir": "/output"
            }
            
            # Run the agent
            result = await agent.run(json.dumps(input_data))
            
            # Verify the agent returned an error message
            assert "response" in result
            assert "error" in result["response"].lower()
            
            # Verify the generate_segment tool was called
            mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_agent_handles_combination_error():
    """Test that the agent handles errors during audio combination."""
    agent = AudioGenerator()
    
    # Create a sample dialogue script
    dialogue_script = [
        {"speaker": "A", "text": "Hello, welcome to our podcast."},
        {"speaker": "B", "text": "Thank you for having me."}
    ]
    
    # Mock paths for generated segments
    segment_paths = [
        "/tmp/segment_1.mp3",
        "/tmp/segment_2.mp3"
    ]
    
    # Mock the generate_audio_segment_tool.run method
    async def mock_generate_segment(*args, **kwargs):
        # Return the appropriate segment path based on call count
        call_count = mock_generate.call_count
        return segment_paths[call_count - 1]
    
    mock_generate = AsyncMock(side_effect=mock_generate_segment)
    
    # Mock the combine_audio_segments_tool.run method to return None (indicating failure)
    mock_combine = AsyncMock(return_value=None)
    
    with patch.object(generate_audio_segment_tool, 'run', mock_generate), \
         patch.object(combine_audio_segments_tool, 'run', mock_combine):
        
        # Mock the LLM response
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
            mock_response = AsyncMock()
            mock_response.text = """
            I successfully generated the individual audio segments:
            - Segment 1: /tmp/segment_1.mp3
            - Segment 2: /tmp/segment_2.mp3
            
            However, I encountered an error when trying to combine these segments.
            The combine_audio_segments tool returned None, indicating a failure.
            Please check the input segments and output directory permissions.
            """
            mock_generate_content.return_value = mock_response
            
            # Create input data for the agent
            input_data = {
                "script": dialogue_script,
                "output_dir": "/output"
            }
            
            # Run the agent
            result = await agent.run(json.dumps(input_data))
            
            # Verify the agent returned an error message
            assert "response" in result
            assert "error" in result["response"].lower() or "failure" in result["response"].lower()
            
            # Verify both tools were called
            assert mock_generate.call_count == 2
            mock_combine.assert_called_once()

@pytest.mark.asyncio
async def test_agent_handles_llm_error():
    """Test that the agent handles LLM errors gracefully."""
    agent = AudioGenerator()
    
    # Create a sample dialogue script
    dialogue_script = [
        {"speaker": "A", "text": "Hello, welcome to our podcast."},
        {"speaker": "B", "text": "Thank you for having me."}
    ]
    
    # Mock the LLM to raise an exception
    with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
        mock_generate_content.side_effect = Exception("API Error")
        
        # Create input data for the agent
        input_data = {
            "script": dialogue_script,
            "output_dir": "/output"
        }
        
        # Run the agent
        result = await agent.run(json.dumps(input_data))
        
        # Verify the agent returned an error response
        assert "error" in result
        assert "API Error" in result["error"]
        
        # Verify the LLM was called
        mock_generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_audio_tools_unit_tests():
    """Unit tests for the actual audio tool functionality."""
    
    # Test segment generation with mocked TextToSpeechAsyncClient
    with patch('google.cloud.texttospeech_v1.TextToSpeechAsyncClient', new_callable=AsyncMock) as mock_client:
        # Configure the mocked client's synthesize_speech method
        mock_instance = mock_client.return_value
        mock_instance.synthesize_speech = AsyncMock()
        mock_response = MagicMock()
        mock_response.audio_content = b'mock audio data'
        mock_instance.synthesize_speech.return_value = mock_response
        
        # Mock aiofiles to avoid actual file operations
        with patch('aiofiles.open', new_callable=AsyncMock) as mock_aiofiles_open:
            # Configure the mock file context manager
            mock_file = AsyncMock()
            mock_aiofiles_open.return_value.__aenter__.return_value = mock_file
            
            # Call the generate_audio_segment_tool with test data
            output_path = await generate_audio_segment_tool.run(
                text="Test speech text",
                speaker="A",
                output_filepath="/tmp/test_output.mp3",
                tts_client=mock_instance
            )
            
            # Verify the right methods were called
            mock_instance.synthesize_speech.assert_called_once()
            # Verify aiofiles.open was called with the correct file path
            mock_aiofiles_open.assert_called_once()
            # Verify write was called with the audio content
            mock_file.write.assert_called_once_with(b'mock audio data')
            
            # Verify the correct output path was returned
            assert output_path == "/tmp/test_output.mp3"
    
    # Test combine_audio_segments with mocked AudioSegment
    with patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('pydub.AudioSegment.from_mp3') as mock_from_mp3, \
         patch('datetime.datetime.now') as mock_now:
        
        # Configure mocks
        mock_segment = MagicMock()
        mock_from_mp3.return_value = mock_segment
        mock_segment.__add__ = lambda _, other: mock_segment  # Mock the sum operation
        mock_now.return_value.strftime.return_value = "20230101_120000"
        
        # Patch the export method
        mock_segment.export = MagicMock()
        
        # Use asyncio.to_thread patch
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = "/output/podcast_digest_20230101_120000.mp3"
            
            # Call the combine_audio_segments_tool with test data
            output_path = await combine_audio_segments_tool.run(
                segment_filepaths=["/tmp/segment_1.mp3", "/tmp/segment_2.mp3"],
                output_dir="/output"
            )
            
            # Verify asyncio.to_thread was called
            mock_to_thread.assert_called_once()
            
            # Verify the correct output path was returned
            assert output_path == "/output/podcast_digest_20230101_120000.mp3" 