"""
Tools related to fetching YouTube transcripts.
"""
import logging
from typing import Dict, List
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from google.adk.tools import tool

logger = logging.getLogger(__name__)

@tool
def fetch_transcript(video_id: str) -> Dict[str, any]:
    """
    Fetch English transcript for a single YouTube video.

    Args:
        video_id (str): YouTube video ID

    Returns:
        Dict[str, any]: Response containing status and either transcript or error message
    """
    try:
        # Use the YouTubeTranscriptApi directly here
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=['en', 'en-US', 'en-GB'],
            preserve_formatting=True
        )

        # Combine all text segments into a single string with timestamps
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
            "result": {
                "transcript": transcript_text,
                "segments": len(transcript_list)
            }
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

@tool
def fetch_transcripts(video_ids: List[str]) -> Dict[str, Dict[str, any]]:
    """
    Fetch English transcripts for multiple YouTube videos.

    Args:
        video_ids (List[str]): List of YouTube video IDs

    Returns:
        Dict[str, Dict[str, any]]: Map of video IDs to their transcripts or error messages
    """
    results = {}

    for video_id in video_ids:
        # Call the standalone fetch_transcript tool function
        results[video_id] = fetch_transcript(video_id)

    return {
        "status": "success",
        "results": results
    } 