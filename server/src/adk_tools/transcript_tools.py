"""
ADK-compatible transcript tools.
"""

import logging
from typing import Any

from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from src.config.proxy_config import ProxyManager

logger = logging.getLogger(__name__)


def fetch_youtube_transcript(video_id: str) -> dict[str, Any]:
    """Fetches the transcript for a single YouTube video.

    Args:
        video_id: The YouTube video ID to fetch transcript for

    Returns:
        Dictionary containing transcript data or error information
    """
    try:
        logger.info(f"Fetching transcript for video: {video_id}")

        # Get proxy configuration
        proxy_config = ProxyManager.get_proxy_config()
        if proxy_config:
            logger.info("Using proxy for transcript fetching")
            # Log proxy type details
            if hasattr(proxy_config, 'retries_when_blocked'):
                logger.info(f"Proxy will retry {proxy_config.retries_when_blocked} times with different IPs")

        # Try different language options
        languages_to_try = [
            ["en", "en-US", "en-GB"],  # English variants
            ["en"],  # Just English
            None,  # Auto-generated
        ]

        transcript_list = None
        last_error = None

        for langs in languages_to_try:
            try:
                if langs:
                    transcript_list = YouTubeTranscriptApi.get_transcript(
                        video_id, languages=langs, proxies=proxy_config
                    )
                else:
                    # Try to get any available transcript
                    transcript_list = YouTubeTranscriptApi.get_transcript(
                        video_id, proxies=proxy_config
                    )
                break
            except Exception as e:
                last_error = e
                continue

        if not transcript_list:
            raise last_error or Exception("No transcript found")

        # Combine transcript segments
        full_transcript = " ".join([entry["text"] for entry in transcript_list])

        logger.info(
            f"Successfully fetched transcript for {video_id} (length: {len(full_transcript)})"
        )
        return {
            "success": True,
            "video_id": video_id,
            "transcript": full_transcript,
            "segment_count": len(transcript_list),
        }

    except (NoTranscriptFound, TranscriptsDisabled) as e:
        logger.warning(f"No transcript available for {video_id}: {e}")
        return {
            "success": False,
            "video_id": video_id,
            "error": f"No transcript available: {e}",
            "transcript": None,
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching transcript for {video_id}: {error_msg}")

        # Provide more specific error messages
        if "no element found" in error_msg.lower():
            error_msg = "YouTube API error. Video may be private/deleted or have disabled captions."
        elif "http error 404" in error_msg.lower():
            error_msg = "Video not found or is not accessible."

        return {
            "success": False,
            "video_id": video_id,
            "error": f"Fetch error: {error_msg}",
            "transcript": None,
        }


def process_multiple_transcripts(video_ids: list[str]) -> dict[str, Any]:
    """Process multiple video transcripts.

    Args:
        video_ids: List of YouTube video IDs

    Returns:
        Dictionary containing all transcript results
    """
    results = {}
    successful_count = 0

    for video_id in video_ids:
        result = fetch_youtube_transcript(video_id)
        results[video_id] = result
        if result["success"]:
            successful_count += 1

    return {
        "results": results,
        "total_videos": len(video_ids),
        "successful_count": successful_count,
        "failed_count": len(video_ids) - successful_count,
    }
