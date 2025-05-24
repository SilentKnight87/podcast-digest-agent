"""
Tools related to fetching YouTube transcripts.
"""

import logging

from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from ..utils.base_tool import Tool

logger = logging.getLogger(__name__)


class TranscriptTool(Tool):
    """Base class for transcript-related tools."""

    def run(self, **kwargs):
        raise NotImplementedError("Tool must implement run method")


class FetchTranscriptTool(TranscriptTool):
    """Tool for fetching a single transcript."""

    name: str = "fetch_transcript"
    description: str = "Fetches the transcript for a single YouTube video"

    def run(self, video_id: str) -> dict[str, any]:
        """Raw implementation for fetching a single transcript."""
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["en", "en-US", "en-GB"], preserve_formatting=True
            )
            transcript_lines = []
            for segment in transcript_list:
                start_time = int(float(segment["start"]))
                text = segment["text"]
                minutes = start_time // 60
                seconds = start_time % 60
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                transcript_lines.append(f"{timestamp} {text}")
            transcript_text = "\n".join(transcript_lines)
            return {"success": True, "transcript": transcript_text, "error": None}
        except (TranscriptsDisabled, NoTranscriptFound) as e:
            logger.warning(f"Transcript fetch failed for {video_id}: {e}")
            return {"success": False, "transcript": None, "error": str(e)}
        except Exception as e:
            # Catch any other unexpected errors during transcript fetching
            logger.error(f"Unexpected error fetching transcript for {video_id}: {e}", exc_info=True)
            return {"success": False, "transcript": None, "error": f"Unexpected error: {e}"}


class FetchTranscriptsTool(TranscriptTool):
    """Tool for fetching multiple transcripts."""

    name: str = "fetch_transcripts"
    description: str = "Fetches transcripts for multiple YouTube videos"

    def run(self, video_ids: list[str]) -> dict[str, dict[str, any]]:
        """Raw implementation for fetching multiple transcripts."""
        results = {}
        single_fetcher = FetchTranscriptTool()  # Create instance once
        for video_id in video_ids:
            # Log the result received from the single fetcher
            single_result = single_fetcher.run(video_id)
            logger.debug(
                f"Transcript fetch result for {video_id}: {single_result}"
            )  # Added logging
            results[video_id] = single_result
        return results


# Create instances of the tools
fetch_transcript = FetchTranscriptTool()
fetch_transcripts = FetchTranscriptsTool()
