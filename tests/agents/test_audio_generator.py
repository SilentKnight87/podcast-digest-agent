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
async def test_agent_run_with_valid_script(tmp_path):
    """Test that the agent can successfully generate audio from a valid script."""
    agent = AudioGenerator()
    print(f"[DEBUG] test_agent_run_with_valid_script: agent.tools = {[t.name for t in agent.tools]}")
    
    dialogue_script = [
        {"speaker": "A", "text": "Hello, welcome to our podcast."},
        {"speaker": "B", "text": "Thank you for having me."}
    ]
    
    # Define a temporary output directory using tmp_path
    test_output_dir = tmp_path / "test_audio_output"
    test_output_dir.mkdir()

    # Mock paths for generated segments (can remain abstract as mock controls them)
    segment_paths = [
        str(tmp_path / "segment_A_0.mp3"), # Using tmp_path for clarity
        str(tmp_path / "segment_B_1.mp3")
    ]
    
    # Final output path should be within the test_output_dir
    final_output_filename = "podcast_digest_20230101_120000.mp3" # Example filename
    final_output_path = str(test_output_dir / final_output_filename)
    
    # Store actual kwargs of calls to generate_audio_segment_tool.run
    generate_calls_kwargs_list = []
    async def mock_generate_segment(*args, **kwargs):
        generate_calls_kwargs_list.append(kwargs.copy())
        call_index = len(generate_calls_kwargs_list) - 1
        return segment_paths[call_index] # Return predefined segment paths
    
    mock_generate = AsyncMock(side_effect=mock_generate_segment)
    
    # Mock the combine_audio_segments_tool.run method
    mock_combine = AsyncMock(return_value=final_output_path)
    
    # Patch the .run() method on the *class* of the tool, not the instance.
    with patch('src.tools.audio_tools.GenerateAudioSegmentTool.run', new=mock_generate), \
         patch('src.tools.audio_tools.CombineAudioSegmentsTool.run', new=mock_combine):
        
        # The LLM mock is not strictly needed if AudioGenerator.run doesn't call it.
        # Kept for now but not asserted.
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
            mock_llm_response_obj = AsyncMock()
            mock_llm_response_obj.text = "LLM response (not directly used for orchestration by the new run method)"
            mock_generate_content.return_value = mock_llm_response_obj
            
            input_data = {
                "script": dialogue_script,
                "output_dir": str(test_output_dir) # Use the temporary path
            }
            
            result = await agent.run(json.dumps(input_data))
            
            assert "response" in result, f"Agent run failed, error: {result.get('error')}"
            assert final_output_path in result["response"]
            
            assert mock_generate.call_count == 2
            
            # Check output_filepath for the first call to generate_audio_segment_tool
            expected_segment_filepath_0 = str(test_output_dir / "segments" / "temp_segment_A_0.mp3")
            assert generate_calls_kwargs_list[0].get('output_filepath') == expected_segment_filepath_0
            
            # Check output_filepath for the second call to generate_audio_segment_tool
            expected_segment_filepath_1 = str(test_output_dir / "segments" / "temp_segment_B_1.mp3")
            assert generate_calls_kwargs_list[1].get('output_filepath') == expected_segment_filepath_1
            
            mock_combine.assert_called_once_with(
                segment_filepaths=segment_paths,
                output_dir=str(test_output_dir)
            )

@pytest.mark.asyncio
async def test_agent_run_with_empty_script(tmp_path):
    """Test that the agent handles an empty script gracefully."""
    agent = AudioGenerator()
    
    dialogue_script = []

    test_output_dir = tmp_path / "test_empty_script_output"
    test_output_dir.mkdir()
    
    # The agent's run method should handle an empty script before attempting to call LLM or tools for generation.
    # So, mocking the LLM might not be necessary if the agent returns early.
    # However, if BaseAgent.run() was called, it would use the LLM.
    # The current AudioGenerator.run() has an early exit for empty scripts.
    with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content: # Kept for now
        mock_llm_response = AsyncMock()
        # This LLM text is what BaseAgent might return if it were called and the script was empty by its logic.
        # AudioGenerator.run has its own specific response for this case.
        mock_llm_response.text = "Cannot process an empty script."
        mock_generate_content.return_value = mock_llm_response
        
        input_data = {
            "script": dialogue_script,
            "output_dir": str(test_output_dir) # Use temporary path
        }
        
        result = await agent.run(json.dumps(input_data))
        
        assert "response" in result
        # AudioGenerator.run returns "Cannot generate audio from an empty script."
        assert "cannot generate audio from an empty script" in result["response"].lower()
        
        # Assert that the LLM was NOT called because AudioGenerator.run handles empty script early
        mock_generate_content.assert_not_called()

@pytest.mark.asyncio
async def test_agent_run_with_invalid_input_format(tmp_path):
    """Test that the agent handles invalid input format gracefully."""
    agent = AudioGenerator()
    
    invalid_input = "This is not a valid JSON string"
    
    # AudioGenerator.run has specific handling for JSONDecodeError before LLM call.
    with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
        # This mock should not be hit.
        mock_llm_response = AsyncMock()
        mock_llm_response.text = "LLM fallback for invalid format (should not be reached)"
        mock_generate_content.return_value = mock_llm_response
        
        result = await agent.run(invalid_input) # output_dir is not part of this invalid input
        
        assert "error" in result
        assert "invalid json input" in result["error"].lower()
        
        mock_generate_content.assert_not_called()

@pytest.mark.asyncio
async def test_agent_handles_segment_generation_error(tmp_path):
    """Test that the agent handles errors during segment generation."""
    agent = AudioGenerator()
    print(f"[DEBUG] test_agent_handles_segment_generation_error: agent.tools = {[t.name for t in agent.tools]}")
    
    dialogue_script = [
        {"speaker": "A", "text": "Hello, welcome to our podcast."},
        {"speaker": "B", "text": "Thank you for having me."}
    ]

    # Define a temporary output directory using tmp_path
    test_output_dir = tmp_path / "test_sg_error_output"
    test_output_dir.mkdir()
    
    # Mock the generate_audio_segment_tool.run method to return None (indicating failure)
    mock_generate = AsyncMock(return_value=None)
    
    with patch('src.tools.audio_tools.GenerateAudioSegmentTool.run', new=mock_generate):
        
        # LLM mock not strictly needed for this specific error path if agent.run handles it directly
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
            # This mock might not be hit if the error occurs before LLM call in agent, or if LLM not used by this path
            mock_llm_response = AsyncMock()
            mock_llm_response.text = "LLM fallback response for segment generation error (may not be used)"
            mock_generate_content.return_value = mock_llm_response
            
            input_data = {
                "script": dialogue_script,
                "output_dir": str(test_output_dir) # Use temporary path
            }
            
            result = await agent.run(json.dumps(input_data))
            
            assert "error" in result # Agent should return an error
            # Check for a more specific error message if possible, e.g., related to segment generation
            assert "generate audio segment" in result["error"].lower() 
            
            # Verify the generate_segment tool was called (even if it failed)
            mock_generate.assert_called_once()
            # We can also check the arguments it was called with, similar to the success test
            args, kwargs = mock_generate.call_args
            expected_segment_filepath = str(test_output_dir / "segments" / "temp_segment_A_0.mp3")
            assert kwargs.get('output_filepath') == expected_segment_filepath

@pytest.mark.asyncio
async def test_agent_handles_combination_error(tmp_path):
    """Test that the agent handles errors during audio combination."""
    agent = AudioGenerator()
    print(f"[DEBUG] test_agent_handles_combination_error: agent.tools = {[t.name for t in agent.tools]}")
    
    dialogue_script = [
        {"speaker": "A", "text": "Hello, welcome to our podcast."},
        {"speaker": "B", "text": "Thank you for having me."}
    ]
    
    # Define a temporary output directory using tmp_path
    test_output_dir = tmp_path / "test_cb_error_output"
    test_output_dir.mkdir()

    # Mock paths for generated segments. These are returned by mock_generate.
    segment_paths = [
        str(test_output_dir / "segments" / "segment_1.mp3"), # Ensure these are plausible if tools were real
        str(test_output_dir / "segments" / "segment_2.mp3")
    ]
    
    # Store actual kwargs of calls to generate_audio_segment_tool.run
    generate_calls_kwargs_list = []
    async def mock_generate_segment(*args, **kwargs):
        generate_calls_kwargs_list.append(kwargs.copy())
        call_index = len(generate_calls_kwargs_list) - 1
        # Return the appropriate segment path based on call count
        return segment_paths[call_index] 
    
    mock_generate = AsyncMock(side_effect=mock_generate_segment)
    
    # Mock the combine_audio_segments_tool.run method to return None (indicating failure)
    mock_combine = AsyncMock(return_value=None)
    
    with patch('src.tools.audio_tools.GenerateAudioSegmentTool.run', new=mock_generate), \
         patch('src.tools.audio_tools.CombineAudioSegmentsTool.run', new=mock_combine):
        
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
            mock_llm_response = AsyncMock()
            mock_llm_response.text = "LLM fallback (may not be used by new run method for this error)"
            mock_generate_content.return_value = mock_llm_response

            input_data = {
                "script": dialogue_script,
                "output_dir": str(test_output_dir) # Use temporary path
            }
            
            result = await agent.run(json.dumps(input_data))
            
            assert "error" in result # Agent should return an error
            assert "failed to combine audio segments" in result["error"].lower()
            
            assert mock_generate.call_count == 2
            # Verify generate_audio_segment_tool calls
            expected_segment_filepath_A0 = str(test_output_dir / "segments" / "temp_segment_A_0.mp3")
            assert generate_calls_kwargs_list[0].get('output_filepath') == expected_segment_filepath_A0
            expected_segment_filepath_B1 = str(test_output_dir / "segments" / "temp_segment_B_1.mp3")
            assert generate_calls_kwargs_list[1].get('output_filepath') == expected_segment_filepath_B1
            
            mock_combine.assert_called_once_with(
                segment_filepaths=segment_paths,
                output_dir=str(test_output_dir)
            )

@pytest.mark.asyncio
async def test_agent_handles_llm_error(tmp_path):
    """Test that the agent handles LLM errors gracefully (currently tests agent's internal error handling)."""
    # Note: This test's name is a misnomer for the current AudioGenerator.run(),
    # as it doesn't call the LLM for its primary orchestration path.
    # It effectively tests internal error handling of AudioGenerator, like tool lookup failure.
    agent = AudioGenerator()
    
    dialogue_script = [
        {"speaker": "A", "text": "Hello, welcome to our podcast."},
        {"speaker": "B", "text": "Thank you for having me."}
    ]

    test_output_dir = tmp_path / "test_llm_error_output"
    test_output_dir.mkdir()
    
    # Mock the LLM to raise an exception - this mock won't be hit by AudioGenerator.run()
    with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate_content:
        mock_generate_content.side_effect = Exception("LLM API Error") # This exception will not be raised
        
        input_data = {
            "script": dialogue_script,
            "output_dir": str(test_output_dir) # Use temporary path
        }
        
        # In this test, tools are NOT mocked to succeed. 
        # AudioGenerator.run() will try to find tools. If it does (they are part of agent.tools),
        # it will then try to call .run() on them. Since .run() is not mocked here to return a value,
        # the real tool .run() would execute, which is not intended for this unit test structure.
        # The most likely failure inside AudioGenerator.run() before any tool execution 
        # if tools are present but their .run() is not mock-patched for *this specific test context* 
        # would be an error during tool execution if they expect mocks or specific environments.
        # However, the agent.tools are instances of GenerateAudioSegmentTool(), etc.
        # Calling their actual .run() would try to use Google Cloud services.

        # Let's assume the agent is correctly initialized with tools. 
        # The previous failure was "Configuration error: generate_audio_segment_tool not found"
        # This implies that the tools *were* being found, but the error message was from a different context.
        # The current AudioGenerator.run() should find the tools by name from self.tools.
        # If we don't patch the tool's .run() methods for *this test specifically*,
        # then the agent will call the *actual* tool.run() methods.
        # This test is not set up for that (e.g. no mocks for TTS client, aiofiles, etc. within the tool.run scope).
        # So, the real tool execution will likely fail.

        # For this test to be meaningful for *AudioGenerator* error handling without LLM,
        # we should simulate a failure in a way that AudioGenerator.run() catches and reports.
        # Example: One of its tools fails to run (returns None).
        # This is already covered by test_agent_handles_segment_generation_error & test_agent_handles_combination_error

        # The original intent was LLM error. Since AudioGenerator.run doesn't use LLM, let's test
        # what happens if a *tool* is misconfigured (e.g., remove one from the agent for this test).
        # This makes it a test of the agent's internal robustness to tool configuration issues.

        original_tools = agent.tools
        agent.tools = [tool for tool in original_tools if tool.name != 'generate_audio_segment'] # Ensure this uses the name as defined in the tool class

        result = await agent.run(json.dumps(input_data))
        
        assert "error" in result
        # Expecting the agent to report that the tool is missing
        assert "generate_audio_segment not found" in result["error"].lower() # Ensure this matches the (new) agent error message format
        
        mock_generate_content.assert_not_called() # LLM should not be called

        agent.tools = original_tools # Restore tools

@pytest.mark.asyncio
async def test_audio_tools_unit_tests():
    """Unit tests for the actual audio tool functionality."""
    
    # Test segment generation with mocked TextToSpeechAsyncClient
    with patch('google.cloud.texttospeech_v1.TextToSpeechAsyncClient', new_callable=AsyncMock) as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.synthesize_speech = AsyncMock()
        mock_tts_response = MagicMock() # Renamed for clarity from mock_response
        mock_tts_response.audio_content = b'mock audio data'
        mock_instance.synthesize_speech.return_value = mock_tts_response
        
        # Corrected mocking for aiofiles.open for async context manager usage
        mock_opened_file = AsyncMock()      # This is the file object yielded by __aenter__
        mock_async_file_context = AsyncMock()
        mock_async_file_context.__aenter__.return_value = mock_opened_file
        mock_async_file_context.__aexit__.return_value = None

        with patch('aiofiles.open', return_value=mock_async_file_context) as mock_aiofiles_open_func:
            output_path = await generate_audio_segment_tool.run(
                text="Test speech text",
                speaker="A",
                output_filepath="/tmp/test_output.mp3",
                tts_client=mock_instance 
            )
            
            mock_instance.synthesize_speech.assert_called_once()
            # Verify aiofiles.open function was called with the correct file path and mode
            mock_aiofiles_open_func.assert_called_once_with("/tmp/test_output.mp3", "wb")
            # Verify write was called on the file object yielded by the context manager
            mock_opened_file.write.assert_called_once_with(b'mock audio data')
            
            assert output_path == "/tmp/test_output.mp3"
    
    # Test combine_audio_segments with mocked AudioSegment
    with patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('pydub.AudioSegment.from_mp3') as mock_from_mp3, \
         patch('src.tools.audio_tools.datetime') as mock_datetime:
        
        # Configure mocks
        mock_segment = MagicMock()
        mock_from_mp3.return_value = mock_segment
        mock_segment.__add__ = lambda _, other: mock_segment  # Mock the sum operation
        mock_datetime.now.return_value.strftime.return_value = "20230101_120000"
        
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