import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from src.agents.transcript_fetcher import TranscriptFetcher
from src.tools.transcript_tools import fetch_transcript, fetch_transcripts
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound

@pytest.fixture
def agent():
    """Creates a TranscriptFetcher agent for testing."""
    return TranscriptFetcher()

@pytest.mark.asyncio
async def test_agent_initialization(agent):
    """Test that the agent initializes with the correct parameters."""
    assert agent.name == "TranscriptFetcher"
    assert "helpful agent that fetches transcripts" in agent.instruction
    assert len(agent.tools) == 2
    assert fetch_transcript in agent.tools
    assert fetch_transcripts in agent.tools

@pytest.mark.asyncio
async def test_agent_run_with_valid_video_id():
    """Test that the agent can successfully fetch a transcript for a valid video ID."""
    agent = TranscriptFetcher()
    
    # Mock the fetch_transcript tool to return a successful result
    mock_transcript = (
        "[00:01] Hello world\n"
        "[00:05] This is a test transcript\n"
        "[00:10] For testing purposes only"
    )
    
    with patch.object(fetch_transcript, 'run') as mock_fetch:
        mock_fetch.return_value = {
            "success": True,
            "transcript": mock_transcript,
            "error": None
        }
        
        # Mock the LLM response
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            mock_response = AsyncMock()
            mock_response.text = "Here is the transcript you requested: " + mock_transcript
            mock_generate.return_value = mock_response
            
            result = await agent.run("Please fetch the transcript for video dQw4w9WgXcQ")
            
            # Verify that the agent returned the expected response
            assert "response" in result
            assert "transcript" in result["response"].lower()
            assert "Hello world" in result["response"]
            
            # Verify that the function was called
            mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_agent_run_with_invalid_video_id():
    """Test that the agent handles errors gracefully when a transcript can't be fetched."""
    agent = TranscriptFetcher()
    
    # Mock the fetch_transcript tool to return an error
    with patch.object(fetch_transcript, 'run') as mock_fetch:
        mock_fetch.return_value = {
            "success": False,
            "transcript": None,
            "error": "No transcript found"
        }
        
        # Mock the LLM response
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            mock_response = AsyncMock()
            mock_response.text = "I'm sorry, I couldn't find a transcript for that video. Error: No transcript found"
            mock_generate.return_value = mock_response
            
            result = await agent.run("Please fetch the transcript for video invalid-id")
            
            # Verify that the agent returned an appropriate error message
            assert "response" in result
            assert "sorry" in result["response"].lower()
            assert "couldn't find" in result["response"].lower()
            
            # Verify that the function was called
            mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_agent_run_with_multiple_videos():
    """Test that the agent can handle requests for multiple videos."""
    agent = TranscriptFetcher()
    
    # Mock the fetch_transcripts tool to return successful results
    mock_transcripts = {
        "video1": {
            "success": True,
            "transcript": "[00:01] Video 1 transcript",
            "error": None
        },
        "video2": {
            "success": True,
            "transcript": "[00:01] Video 2 transcript",
            "error": None
        }
    }
    
    with patch.object(fetch_transcripts, 'run') as mock_fetch:
        mock_fetch.return_value = mock_transcripts
        
        # Mock the LLM response
        with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
            mock_response = AsyncMock()
            mock_response.text = "Here are the transcripts for the videos you requested:\n\nVideo 1:\n[00:01] Video 1 transcript\n\nVideo 2:\n[00:01] Video 2 transcript"
            mock_generate.return_value = mock_response
            
            result = await agent.run("Please fetch transcripts for videos video1 and video2")
            
            # Verify that the agent returned the expected response
            assert "response" in result
            assert "Video 1" in result["response"]
            assert "Video 2" in result["response"]
            
            # Verify that the function was called
            mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_agent_run_with_llm_error():
    """Test that the agent handles LLM errors gracefully."""
    agent = TranscriptFetcher()
    
    # Mock the LLM to raise an exception
    with patch('google.generativeai.GenerativeModel.generate_content_async') as mock_generate:
        mock_generate.side_effect = Exception("API Error")
        
        result = await agent.run("Please fetch the transcript for video dQw4w9WgXcQ")
        
        # Verify that the agent returned an error response
        assert "error" in result
        assert "API Error" in result["error"]
        
        # Verify that the function was called
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_transcript_tool_with_real_exception():
    """Test the behavior of the fetch_transcript tool when YouTube API raises exceptions."""
    # Test with TranscriptsDisabled exception
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript') as mock_get_transcript:
        mock_get_transcript.side_effect = TranscriptsDisabled("Transcripts are disabled for this video")
        
        result = fetch_transcript.run(video_id="some-id")
        
        assert result["success"] is False
        assert result["transcript"] is None
        assert "disabled" in result["error"].lower()

    # Test with NoTranscriptFound exception
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript') as mock_get_transcript:
        mock_get_transcript.side_effect = NoTranscriptFound("No transcript was found")
        
        result = fetch_transcript.run(video_id="some-id")
        
        assert result["success"] is False
        assert result["transcript"] is None
        assert "no transcript" in result["error"].lower()

    # Test with an unexpected exception
    with patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript') as mock_get_transcript:
        mock_get_transcript.side_effect = Exception("Unexpected error")
        
        result = fetch_transcript.run(video_id="some-id")
        
        assert result["success"] is False
        assert result["transcript"] is None
        assert "unexpected error" in result["error"].lower() 