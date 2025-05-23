"""
Tests for transcript fetching tools.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock

# Module to test
from src.tools.transcript_tools import (
    fetch_transcript,  # The Tool instance
    fetch_transcripts  # The Tool instance
)
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound

# Mock transcript data - using objects like the real API
class MockTranscriptSegment:
    def __init__(self, text, start, duration=1.5):
        self.text = text
        self.start = start
        self.duration = duration

# Create mock segments that behave like the real API objects
MOCK_TRANSCRIPT_SEGMENTS = [
    MockTranscriptSegment('Hello world', 0.5),
    MockTranscriptSegment('Testing 123', 3.0)
]

EXPECTED_TRANSCRIPT_TEXT = "[00:00] Hello world\n[00:03] Testing 123"

# --- Tests for fetch_transcript --- 

@patch('youtube_transcript_api.YouTubeTranscriptApi.list_transcripts')
def test_fetch_transcript_success_manual(mock_list_transcripts):
    """Test successful transcript fetching with manual transcript."""
    video_id = "valid_id"
    
    # Mock the transcript list object
    mock_transcript_list = Mock()
    mock_list_transcripts.return_value = mock_transcript_list
    
    # Mock a manual transcript
    mock_transcript = Mock()
    mock_transcript.fetch.return_value = MOCK_TRANSCRIPT_SEGMENTS
    mock_transcript.language = 'en'
    
    # Set up the find methods
    mock_transcript_list.find_manually_created_transcript.return_value = mock_transcript
    
    result = fetch_transcript.run(video_id=video_id)
    
    mock_list_transcripts.assert_called_once_with(video_id)
    mock_transcript_list.find_manually_created_transcript.assert_called_once_with(['en', 'en-US', 'en-GB'])
    
    assert result["success"] is True
    assert result["transcript"] == EXPECTED_TRANSCRIPT_TEXT
    assert result["error"] is None

@patch('youtube_transcript_api.YouTubeTranscriptApi.list_transcripts')
def test_fetch_transcript_success_generated(mock_list_transcripts):
    """Test successful transcript fetching with auto-generated transcript."""
    video_id = "valid_id"
    
    # Mock the transcript list object
    mock_transcript_list = Mock()
    mock_list_transcripts.return_value = mock_transcript_list
    
    # Mock no manual transcript but has generated
    mock_transcript_list.find_manually_created_transcript.side_effect = NoTranscriptFound(
        video_id, ['en', 'en-US', 'en-GB'], None
    )
    
    # Mock a generated transcript
    mock_transcript = Mock()
    mock_transcript.fetch.return_value = MOCK_TRANSCRIPT_SEGMENTS
    mock_transcript.language = 'en'
    mock_transcript_list.find_generated_transcript.return_value = mock_transcript
    
    result = fetch_transcript.run(video_id=video_id)
    
    assert result["success"] is True
    assert result["transcript"] == EXPECTED_TRANSCRIPT_TEXT
    assert result["error"] is None

@patch('youtube_transcript_api.YouTubeTranscriptApi.list_transcripts')
def test_fetch_transcript_fallback_any_language(mock_list_transcripts):
    """Test transcript fetching falls back to any available language."""
    video_id = "valid_id"
    
    # Mock the transcript list object
    mock_transcript_list = Mock()
    mock_list_transcripts.return_value = mock_transcript_list
    
    # Mock no English transcripts
    mock_transcript_list.find_manually_created_transcript.side_effect = NoTranscriptFound(
        video_id, ['en', 'en-US', 'en-GB'], None
    )
    mock_transcript_list.find_generated_transcript.side_effect = NoTranscriptFound(
        video_id, ['en', 'en-US', 'en-GB'], None
    )
    
    # Mock a transcript in another language
    mock_transcript = Mock()
    mock_transcript.fetch.return_value = MOCK_TRANSCRIPT_SEGMENTS
    mock_transcript.language = 'es'
    
    # Make the transcript list iterable
    mock_transcript_list.__iter__ = Mock(return_value=iter([mock_transcript]))
    
    result = fetch_transcript.run(video_id=video_id)
    
    assert result["success"] is True
    assert result["transcript"] == EXPECTED_TRANSCRIPT_TEXT
    assert result["error"] is None

@patch('youtube_transcript_api.YouTubeTranscriptApi.list_transcripts')
def test_fetch_transcript_disabled(mock_list_transcripts):
    """Test handling TranscriptsDisabled error."""
    video_id = "disabled_id"
    mock_list_transcripts.side_effect = TranscriptsDisabled(video_id)
    
    result = fetch_transcript.run(video_id=video_id)
    
    assert result["success"] is False
    assert result["transcript"] is None
    assert "Transcripts are disabled" in result["error"]

@patch('youtube_transcript_api.YouTubeTranscriptApi.list_transcripts')
def test_fetch_transcript_not_found(mock_list_transcripts):
    """Test handling when no transcripts available."""
    video_id = "not_found_id"
    
    # Mock the transcript list object
    mock_transcript_list = Mock()
    mock_list_transcripts.return_value = mock_transcript_list
    
    # Mock no transcripts available
    mock_transcript_list.find_manually_created_transcript.side_effect = NoTranscriptFound(
        video_id, ['en', 'en-US', 'en-GB'], None
    )
    mock_transcript_list.find_generated_transcript.side_effect = NoTranscriptFound(
        video_id, ['en', 'en-US', 'en-GB'], None
    )
    mock_transcript_list.__iter__ = Mock(return_value=iter([]))  # No transcripts
    
    result = fetch_transcript.run(video_id=video_id)
    
    assert result["success"] is False
    assert result["transcript"] is None
    assert "No transcript found" in result["error"]

@patch('youtube_transcript_api.YouTubeTranscriptApi.list_transcripts')
def test_fetch_transcript_xml_parse_error(mock_list_transcripts):
    """Test handling XML parse error (private/deleted video)."""
    video_id = "private_id"
    
    # Simulate the XML parse error
    from xml.etree.ElementTree import ParseError
    mock_list_transcripts.side_effect = ParseError("no element found: line 1, column 0")
    
    result = fetch_transcript.run(video_id=video_id)
    
    assert result["success"] is False
    assert result["transcript"] is None
    assert "YouTube returned invalid data" in result["error"]
    assert "private, deleted, or have restricted access" in result["error"]

@patch('youtube_transcript_api.YouTubeTranscriptApi.list_transcripts')
def test_fetch_transcript_handles_dict_format(mock_list_transcripts):
    """Test that code still handles dictionary format for backward compatibility."""
    video_id = "valid_id"
    
    # Mock the transcript list object
    mock_transcript_list = Mock()
    mock_list_transcripts.return_value = mock_transcript_list
    
    # Mock a manual transcript that returns dictionaries (old format)
    mock_transcript = Mock()
    mock_transcript.fetch.return_value = [
        {'text': 'Hello world', 'start': 0.5, 'duration': 1.5},
        {'text': 'Testing 123', 'start': 3.0, 'duration': 2.0}
    ]
    mock_transcript.language = 'en'
    mock_transcript_list.find_manually_created_transcript.return_value = mock_transcript
    
    result = fetch_transcript.run(video_id=video_id)
    
    assert result["success"] is True
    assert result["transcript"] == EXPECTED_TRANSCRIPT_TEXT
    assert result["error"] is None

# --- Tests for fetch_transcripts --- 

@patch('src.tools.transcript_tools.FetchTranscriptTool.run')
def test_fetch_transcripts(mock_fetch_run):
    """Test fetching multiple transcripts."""
    video_ids = ["id1", "id2"]
    
    # Mock successful transcript for first video, failure for second
    mock_fetch_run.side_effect = [
        {
            "success": True,
            "transcript": EXPECTED_TRANSCRIPT_TEXT,
            "error": None
        },
        {
            "success": False,
            "transcript": None,
            "error": "No transcript found for video id2"
        }
    ]
    
    result = fetch_transcripts.run(video_ids=video_ids)
    
    assert len(result) == 2
    # Check first video result
    assert result["id1"]["success"] is True
    assert result["id1"]["transcript"] == EXPECTED_TRANSCRIPT_TEXT
    assert result["id1"]["error"] is None
    # Check second video result
    assert result["id2"]["success"] is False
    assert result["id2"]["transcript"] is None
    assert "No transcript found" in result["id2"]["error"]

# --- Tests for Tool instances ---

def test_fetch_transcript_tool_instance():
    """Verify the fetch_transcript Tool instance."""
    assert fetch_transcript.name == "fetch_transcript"
    assert "Fetches the transcript" in fetch_transcript.description

def test_fetch_transcripts_tool_instance():
    """Verify the fetch_transcripts Tool instance."""
    assert fetch_transcripts.name == "fetch_transcripts"
    assert "Fetches transcripts" in fetch_transcripts.description