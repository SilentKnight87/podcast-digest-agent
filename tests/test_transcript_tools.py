"""
Tests for transcript fetching tools.
"""
from unittest.mock import patch

from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled

# Module to test
from src.tools.transcript_tools import (
    fetch_transcript,  # The Tool instance
    fetch_transcripts,  # The Tool instance
)

# Mock transcript data
SAMPLE_TRANSCRIPT_LIST = [
    {"text": "Hello world", "start": 0.5, "duration": 1.5},
    {"text": "Testing 123", "start": 3.0, "duration": 2.0},
]
EXPECTED_TRANSCRIPT_TEXT = "[00:00] Hello world\n[00:03] Testing 123"

# --- Tests for fetch_transcript ---


@patch("youtube_transcript_api.YouTubeTranscriptApi.get_transcript")
def test_fetch_transcript_success(mock_get_transcript):
    """Test successful transcript fetching."""
    mock_get_transcript.return_value = SAMPLE_TRANSCRIPT_LIST
    video_id = "valid_id"

    result = fetch_transcript.run(video_id=video_id)

    mock_get_transcript.assert_called_once_with(
        video_id, languages=["en", "en-US", "en-GB"], preserve_formatting=True
    )
    assert result["success"] is True
    assert result["transcript"] == EXPECTED_TRANSCRIPT_TEXT
    assert result["error"] is None


@patch("youtube_transcript_api.YouTubeTranscriptApi.get_transcript")
def test_fetch_transcript_disabled(mock_get_transcript):
    """Test handling TranscriptsDisabled error."""
    video_id = "disabled_id"
    mock_get_transcript.side_effect = TranscriptsDisabled(video_id)

    result = fetch_transcript.run(video_id=video_id)

    assert result["success"] is False
    assert result["transcript"] is None
    assert "Transcripts are disabled" in result["error"]


@patch("youtube_transcript_api.YouTubeTranscriptApi.get_transcript")
def test_fetch_transcript_not_found(mock_get_transcript):
    """Test handling NoTranscriptFound error."""
    video_id = "not_found_id"
    mock_get_transcript.side_effect = NoTranscriptFound(video_id, ["en"], None)

    result = fetch_transcript.run(video_id=video_id)

    assert result["success"] is False
    assert result["transcript"] is None
    assert "No transcript found" in result["error"]


# --- Tests for fetch_transcripts ---


@patch("youtube_transcript_api.YouTubeTranscriptApi.get_transcript")
def test_fetch_transcripts(mock_get_transcript):
    """Test fetching multiple transcripts."""
    video_ids = ["id1", "id2"]

    # Mock successful transcript for first video
    mock_get_transcript.side_effect = [
        SAMPLE_TRANSCRIPT_LIST,  # For id1
        NoTranscriptFound("id2", ["en"], None),  # For id2
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


# Remove placeholder test
# def test_placeholder():
#     """Placeholder test."""
#     assert True
