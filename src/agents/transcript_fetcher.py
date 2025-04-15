"""
TranscriptFetcher Agent for fetching YouTube transcripts using Google ADK.
"""
import logging
from typing import Dict, Optional, List
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from google.cloud.adk import Agent, tool

logger = logging.getLogger(__name__)

class TranscriptFetcher(Agent):
    """Agent responsible for fetching transcripts from YouTube videos."""
    
    def __init__(self):
        """Initialize the TranscriptFetcher agent."""
        super().__init__()
        self.transcript_api = YouTubeTranscriptApi
        self.name = "TranscriptFetcher"
        self.description = "Agent that fetches and processes YouTube video transcripts"
        self.instructions = """You are a helpful agent that fetches transcripts from YouTube videos.
        When given a video ID or URL, you will attempt to fetch its transcript and format it nicely.
        If there are any errors, you will explain them clearly to the user."""
    
    @tool
    def fetch_transcript(self, video_id: str) -> Dict[str, any]:
        """
        Fetch English transcript for a single YouTube video.
        
        Args:
            video_id (str): YouTube video ID
            
        Returns:
            Dict[str, any]: Response containing status and either transcript or error message
        """
        try:
            # Get the transcript
            transcript_list = self.transcript_api.get_transcript(
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
    def fetch_transcripts(self, video_ids: List[str]) -> Dict[str, Dict[str, any]]:
        """
        Fetch English transcripts for multiple YouTube videos.
        
        Args:
            video_ids (List[str]): List of YouTube video IDs
            
        Returns:
            Dict[str, Dict[str, any]]: Map of video IDs to their transcripts or error messages
        """
        results = {}
        
        for video_id in video_ids:
            results[video_id] = self.fetch_transcript(video_id)
            
        return {
            "status": "success",
            "results": results
        } 