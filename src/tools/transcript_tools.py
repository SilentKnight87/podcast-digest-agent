"""
Tools related to fetching YouTube transcripts.
"""
import logging
from typing import Dict, List
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Import FunctionTool
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

# Define the raw Python functions first
def _fetch_transcript_impl(video_id: str) -> Dict[str, any]:
    """Raw implementation for fetching a single transcript."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=['en', 'en-US', 'en-GB'],
            preserve_formatting=True
        )
        transcript_lines = []
        for segment in transcript_list:
            start_time = int(float(segment['start']))
            text = segment['text']
            minutes = start_time // 60
            seconds = start_time % 60
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            transcript_lines.append(f"{timestamp} {text}")
        transcript_text = "\n".join(transcript_lines)
        logger.info(f"Successfully fetched English transcript for video {video_id}")
        return {
            "status": "success",
            "result": {"transcript": transcript_text, "segments": len(transcript_list)}
        }
    except TranscriptsDisabled:
        error_msg = f"Transcripts are disabled for video {video_id}"
        logger.warning(error_msg)
        return {"status": "error", "error": error_msg}
    except NoTranscriptFound:
        error_msg = f"No transcript found for video {video_id}"
        logger.warning(error_msg)
        return {"status": "error", "error": error_msg}
    except Exception as e:
        error_msg = f"Error fetching transcript for video {video_id}: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}

def _fetch_transcripts_impl(video_ids: List[str]) -> Dict[str, Dict[str, any]]:
    """Raw implementation for fetching multiple transcripts."""
    results = {}
    for video_id in video_ids:
        results[video_id] = _fetch_transcript_impl(video_id) # Call the raw impl
    # FunctionTool expects a single return value, so we wrap the dict
    # ADK might handle dicts directly, but let's ensure compatibility
    return {"status": "success", "results": results}

# Now, create FunctionTool instances from the raw functions
# Passing only the function, assuming name/description are inferred
fetch_transcript = FunctionTool(
    func=_fetch_transcript_impl
    # description="Fetch English transcript for a single YouTube video."
)

fetch_transcripts = FunctionTool(
    func=_fetch_transcripts_impl
    # description="Fetch English transcripts for multiple YouTube videos."
) 