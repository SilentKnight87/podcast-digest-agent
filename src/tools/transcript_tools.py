"""
Tools related to fetching YouTube transcripts.
"""
import logging
from typing import Dict, List, Optional
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, TranscriptList

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

    def run(self, video_id: str) -> Dict[str, any]:
        """Raw implementation for fetching a single transcript."""
        try:
            # First try to list available transcripts
            transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to find a suitable transcript
            transcript = None
            try:
                # First try manual transcripts in English
                transcript = transcript_list_obj.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
            except NoTranscriptFound:
                try:
                    # Fall back to auto-generated transcripts
                    transcript = transcript_list_obj.find_generated_transcript(['en', 'en-US', 'en-GB'])
                except NoTranscriptFound:
                    # Try to get any available transcript
                    try:
                        # Get the first available transcript in any language
                        available_transcripts = list(transcript_list_obj)
                        if available_transcripts:
                            transcript = available_transcripts[0]
                            logger.warning(f"Using transcript in language: {transcript.language} for video {video_id}")
                    except Exception:
                        pass
            
            if transcript is None:
                raise NoTranscriptFound(video_id, ['en', 'en-US', 'en-GB'], None)
            
            # Fetch the actual transcript content
            transcript_list = transcript.fetch()
            transcript_lines = []
            for segment in transcript_list:
                # Handle both dict and object formats
                if hasattr(segment, 'start'):
                    start_time = int(float(segment.start))
                    text = segment.text
                else:
                    start_time = int(float(segment['start']))
                    text = segment['text']
                    
                minutes = start_time // 60
                seconds = start_time % 60
                timestamp = f"[{minutes:02d}:{seconds:02d}]"
                transcript_lines.append(f"{timestamp} {text}")
            transcript_text = "\n".join(transcript_lines)
            return {
                "success": True,
                "transcript": transcript_text,
                "error": None
            }
        except TranscriptsDisabled:
            error_msg = f"Transcripts are disabled for video {video_id}"
            logger.warning(error_msg)
            return {
                "success": False,
                "transcript": None,
                "error": error_msg
            }
        except NoTranscriptFound:
            error_msg = f"No transcript found for video {video_id}"
            logger.warning(error_msg)
            return {
                "success": False,
                "transcript": None,
                "error": error_msg
            }
        except Exception as e:
            # Catch any other unexpected errors during transcript fetching
            error_msg = str(e)
            if "no element found" in error_msg:
                error_msg = f"YouTube returned invalid data for video {video_id}. The video may be private, deleted, or have restricted access."
            logger.error(f"Unexpected error fetching transcript for {video_id}: {error_msg}")
            return {
                "success": False,
                "transcript": None,
                "error": error_msg
            }

class FetchTranscriptsTool(TranscriptTool):
    """Tool for fetching multiple transcripts."""
    name: str = "fetch_transcripts"
    description: str = "Fetches transcripts for multiple YouTube videos"

    def run(self, video_ids: List[str]) -> Dict[str, Dict[str, any]]:
        """Raw implementation for fetching multiple transcripts."""
        results = {}
        single_fetcher = FetchTranscriptTool() # Create instance once
        for video_id in video_ids:
            # Log the result received from the single fetcher
            single_result = single_fetcher.run(video_id)
            logger.debug(f"Transcript fetch result for {video_id}: {single_result}") # Added logging
            results[video_id] = single_result
        return results

# Create instances of the tools
fetch_transcript = FetchTranscriptTool()
fetch_transcripts = FetchTranscriptsTool() 