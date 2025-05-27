"""
Tests for ADK-compatible transcript tools.
"""
from unittest.mock import patch

from src.adk_tools.transcript_tools import fetch_youtube_transcript, process_multiple_transcripts


class TestFetchYoutubeTranscript:
    """Test fetch_youtube_transcript function."""

    def test_successful_transcript_fetch(self):
        """Test successful transcript fetch."""
        with patch("src.adk_tools.transcript_tools.YouTubeTranscriptApi") as mock_api:
            # Mock successful transcript
            mock_api.get_transcript.return_value = [
                {"text": "Hello", "start": 0.0, "duration": 1.0},
                {"text": "world", "start": 1.0, "duration": 1.0},
            ]

            result = fetch_youtube_transcript("test_video_id")

            assert result["success"] is True
            assert result["video_id"] == "test_video_id"
            assert result["transcript"] == "Hello world"
            assert result["segment_count"] == 2

            # Verify API was called correctly
            mock_api.get_transcript.assert_called_once_with(
                "test_video_id", languages=["en", "en-US", "en-GB"]
            )

    def test_no_transcript_found(self):
        """Test handling of no transcript found."""
        with patch("src.adk_tools.transcript_tools.YouTubeTranscriptApi") as mock_api:
            from youtube_transcript_api import NoTranscriptFound

            mock_api.get_transcript.side_effect = NoTranscriptFound("test_video_id", ["en"], ["en"])

            result = fetch_youtube_transcript("test_video_id")

            assert result["success"] is False
            assert result["video_id"] == "test_video_id"
            assert "No transcript available" in result["error"]
            assert result["transcript"] is None

    def test_transcripts_disabled(self):
        """Test handling of disabled transcripts."""
        with patch("src.adk_tools.transcript_tools.YouTubeTranscriptApi") as mock_api:
            from youtube_transcript_api import TranscriptsDisabled

            mock_api.get_transcript.side_effect = TranscriptsDisabled("test_video_id")

            result = fetch_youtube_transcript("test_video_id")

            assert result["success"] is False
            assert result["video_id"] == "test_video_id"
            assert "No transcript available" in result["error"]
            assert result["transcript"] is None

    def test_general_exception(self):
        """Test handling of general exceptions."""
        with patch("src.adk_tools.transcript_tools.YouTubeTranscriptApi") as mock_api:
            mock_api.get_transcript.side_effect = Exception("Network error")

            result = fetch_youtube_transcript("test_video_id")

            assert result["success"] is False
            assert result["video_id"] == "test_video_id"
            assert "Fetch error: Network error" in result["error"]
            assert result["transcript"] is None


class TestProcessMultipleTranscripts:
    """Test process_multiple_transcripts function."""

    def test_process_multiple_success(self):
        """Test processing multiple transcripts successfully."""
        with patch("src.adk_tools.transcript_tools.fetch_youtube_transcript") as mock_fetch:
            # Mock two successful and one failed transcript
            mock_fetch.side_effect = [
                {
                    "success": True,
                    "video_id": "video1",
                    "transcript": "Content 1",
                    "segment_count": 10,
                },
                {
                    "success": False,
                    "video_id": "video2",
                    "error": "No transcript",
                    "transcript": None,
                },
                {
                    "success": True,
                    "video_id": "video3",
                    "transcript": "Content 3",
                    "segment_count": 20,
                },
            ]

            result = process_multiple_transcripts(["video1", "video2", "video3"])

            assert result["total_videos"] == 3
            assert result["successful_count"] == 2
            assert result["failed_count"] == 1
            assert len(result["results"]) == 3
            assert result["results"]["video1"]["success"] is True
            assert result["results"]["video2"]["success"] is False
            assert result["results"]["video3"]["success"] is True

    def test_process_empty_list(self):
        """Test processing empty video list."""
        result = process_multiple_transcripts([])

        assert result["total_videos"] == 0
        assert result["successful_count"] == 0
        assert result["failed_count"] == 0
        assert result["results"] == {}

    def test_process_single_video(self):
        """Test processing single video."""
        with patch("src.adk_tools.transcript_tools.fetch_youtube_transcript") as mock_fetch:
            mock_fetch.return_value = {
                "success": True,
                "video_id": "single_video",
                "transcript": "Single content",
                "segment_count": 5,
            }

            result = process_multiple_transcripts(["single_video"])

            assert result["total_videos"] == 1
            assert result["successful_count"] == 1
            assert result["failed_count"] == 0
            assert "single_video" in result["results"]
