"""
Tests for transcript fetching tools.
"""
import pytest
from unittest.mock import patch, MagicMock

# Module to test
from src.tools.transcript_tools import (
    _fetch_transcript_impl,
    _fetch_transcripts_impl,
    fetch_transcript, # The FunctionTool instance
    fetch_transcripts # The FunctionTool instance
)
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
from google.adk.tools import FunctionTool

# Mock transcript data
SAMPLE_TRANSCRIPT_LIST = [
    {'text': 'Hello world', 'start': 0.5, 'duration': 1.5},
    {'text': 'Testing 123', 'start': 3.0, 'duration': 2.0}
]
EXPECTED_TRANSCRIPT_TEXT = "[00:00] Hello world\n[00:03] Testing 123"

# --- Tests for _fetch_transcript_impl --- 

@patch('src.tools.transcript_tools.YouTubeTranscriptApi.get_transcript')
def test_fetch_transcript_impl_success(mock_get_transcript):
    """Test successful transcript fetching."""
    mock_get_transcript.return_value = SAMPLE_TRANSCRIPT_LIST
    video_id = "valid_id"
    
    result = _fetch_transcript_impl(video_id)
    
    mock_get_transcript.assert_called_once_with(
        video_id,
        languages=['en', 'en-US', 'en-GB'],
        preserve_formatting=True
    )
    assert result["status"] == "success"
    assert result["result"]["transcript"] == EXPECTED_TRANSCRIPT_TEXT
    assert result["result"]["segments"] == 2

@patch('src.tools.transcript_tools.YouTubeTranscriptApi.get_transcript')
def test_fetch_transcript_impl_disabled(mock_get_transcript):
    """Test handling TranscriptsDisabled error."""
    video_id = "disabled_id"
    mock_get_transcript.side_effect = TranscriptsDisabled(video_id)
    
    result = _fetch_transcript_impl(video_id)
    
    assert result["status"] == "error"
    assert "Transcripts are disabled" in result["error"]
    assert video_id in result["error"]

@patch('src.tools.transcript_tools.YouTubeTranscriptApi.get_transcript')
def test_fetch_transcript_impl_not_found(mock_get_transcript):
    """Test handling NoTranscriptFound error."""
    video_id = "not_found_id"
    mock_get_transcript.side_effect = NoTranscriptFound(video_id, ['en'], None)
    
    result = _fetch_transcript_impl(video_id)
    
    assert result["status"] == "error"
    assert "No transcript found" in result["error"]
    assert video_id in result["error"]

@patch('src.tools.transcript_tools.YouTubeTranscriptApi.get_transcript')
def test_fetch_transcript_impl_generic_error(mock_get_transcript):
    """Test handling other exceptions."""
    video_id = "error_id"
    error_message = "Something went wrong"
    mock_get_transcript.side_effect = Exception(error_message)
    
    result = _fetch_transcript_impl(video_id)
    
    assert result["status"] == "error"
    assert "Error fetching transcript" in result["error"]
    assert error_message in result["error"]
    assert video_id in result["error"]

# --- Tests for _fetch_transcripts_impl --- 

@patch('src.tools.transcript_tools._fetch_transcript_impl')
def test_fetch_transcripts_impl(mock_fetch_single):
    """Test fetching multiple transcripts, mocking the single fetch."""
    video_ids = ["id1", "id2", "id3"]
    
    # Define mock return values for each call to the single fetch
    mock_fetch_single.side_effect = [
        {"status": "success", "result": {"transcript": "t1", "segments": 1}}, # For id1
        {"status": "error", "error": "disabled"}, # For id2
        {"status": "success", "result": {"transcript": "t3", "segments": 5}}, # For id3
    ]
    
    result = _fetch_transcripts_impl(video_ids)
    
    # Verify the single fetch was called for each ID
    assert mock_fetch_single.call_count == 3
    mock_fetch_single.assert_any_call("id1")
    mock_fetch_single.assert_any_call("id2")
    mock_fetch_single.assert_any_call("id3")
    
    # Verify the overall result structure
    assert result["status"] == "success"
    assert "results" in result
    results_map = result["results"]
    assert len(results_map) == 3
    
    # Check individual results within the map
    assert results_map["id1"]["status"] == "success"
    assert results_map["id1"]["result"]["transcript"] == "t1"
    assert results_map["id2"]["status"] == "error"
    assert results_map["id2"]["error"] == "disabled"
    assert results_map["id3"]["status"] == "success"
    assert results_map["id3"]["result"]["transcript"] == "t3"

# --- Tests for FunctionTool instances ---

def test_fetch_transcript_function_tool_instance():
    """Verify the fetch_transcript FunctionTool instance."""
    # Check type if FunctionTool is accessible for isinstance check
    # from google.adk.tools import FunctionTool # Already imported
    assert isinstance(fetch_transcript, FunctionTool)
    # Check that the name is inferred correctly from the wrapped function
    assert fetch_transcript.name == "_fetch_transcript_impl"
    # Check that the wrapped function is correct
    assert fetch_transcript.func == _fetch_transcript_impl

def test_fetch_transcripts_function_tool_instance():
    """Verify the fetch_transcripts FunctionTool instance."""
    assert isinstance(fetch_transcripts, FunctionTool)
    assert fetch_transcripts.name == "_fetch_transcripts_impl"
    assert fetch_transcripts.func == _fetch_transcripts_impl

# Remove placeholder test
# def test_placeholder():
#     """Placeholder test."""
#     assert True 