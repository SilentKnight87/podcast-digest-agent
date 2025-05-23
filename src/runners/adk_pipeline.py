"""
Agent Development Kit (ADK) based pipeline runner for podcast digest generation.
Implements event streaming and session management from ADK April 2025 release.
"""
import logging
import asyncio
import tempfile
from typing import List, Dict, Any, AsyncGenerator
from pathlib import Path

from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import Session, InMemorySessionService
from google.adk.events import Event
from google.genai.types import Content, Part, UserContent
from google.cloud import texttospeech_v1

# Import ADK agents
from ..agents.adk_agents import podcast_pipeline

logger = logging.getLogger(__name__)

class AdkPipelineRunner:
    """
    ADK-based pipeline runner that orchestrates the complete podcast digest workflow.
    
    This class:
    1. Initializes the ADK runner with our pipeline
    2. Creates sessions for each processing job
    3. Streams events as agents work
    4. Returns the final results
    """
    
    def __init__(self):
        """Initialize the ADK pipeline runner."""
        # Use InMemoryRunner for local execution
        self.runner = InMemoryRunner(agent=podcast_pipeline)
        self.session_service = self.runner.session_service
        self.temp_dirs = []
        logger.info("ADK Pipeline Runner initialized")
    
    async def run_async(self, video_ids: List[str], output_dir: str) -> Dict[str, Any]:
        """
        Run the complete podcast digest pipeline using Google ADK.
        
        Args:
            video_ids: List of YouTube video IDs to process
            output_dir: Directory for final audio output
            
        Returns:
            Dictionary containing results and status information
        """
        logger.info(f"Starting ADK pipeline for {len(video_ids)} videos")
        
        try:
            # Initialize Google Cloud TTS client
            async with texttospeech_v1.TextToSpeechAsyncClient() as tts_client:
                # Create ADK session with initial state
                initial_state = {
                    "video_ids": video_ids,
                    "output_dir": output_dir,
                    "tts_client": tts_client
                }
                
                # Create session using session service
                session = await self.session_service.create_session(
                    app_name="podcast_digest_app",
                    user_id="system",
                    session_id=f"session_{asyncio.get_event_loop().time()}",
                    state=initial_state
                )
                
                # Create temporary directory for audio processing
                temp_dir = tempfile.mkdtemp(prefix="adk_podcast_segments_")
                self.temp_dirs.append(temp_dir)
                
                # Update session state
                await self.session_service.update_state(
                    app_name="podcast_digest_app",
                    user_id="system",
                    session_id=session.id,
                    state_delta={"temp_dir": temp_dir}
                )
                
                logger.info("ADK session initialized with state")
                
                # Prepare user message
                user_message = UserContent(
                    parts=[Part(text=f"Process YouTube videos with IDs: {video_ids}")]
                )
                
                # Run the ADK pipeline with event streaming
                logger.info("Starting ADK pipeline execution")
                final_audio_path = None
                dialogue_script = []
                summaries = []
                transcripts = {}
                
                # Stream events from the pipeline
                # This is the CORE PATTERN of ADK - async event streaming!
                async for event in self.runner.run_async(
                    user_id="system",
                    session_id=session.id,
                    new_message=user_message
                ):
                    # Each event represents something happening:
                    # - Agent thinking
                    # - Tool being called
                    # - State being updated
                    # - Final response
                    
                    if event.is_final_response():
                        logger.info(f"Final response from {event.author}")
                    
                    # Log intermediate results for debugging
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                logger.debug(f"Event from {event.author}: {part.text[:100]}...")
                    
                    # You could also:
                    # - Send progress updates to frontend
                    # - Save intermediate results
                    # - Handle errors in real-time
                
                # Get final session state after pipeline completion
                final_session = await self.session_service.get_session(
                    app_name="podcast_digest_app",
                    user_id="system",
                    session_id=session.id
                )
                
                # Extract results from final session state
                final_audio_path = final_session.state.get("final_audio_path")
                dialogue_script = final_session.state.get("dialogue_script", [])
                summaries = final_session.state.get("summaries", [])
                transcripts = final_session.state.get("transcripts", {})
                
                logger.info(f"ADK pipeline completed. Audio path: {final_audio_path}")
                
                # Process and return results
                if final_audio_path:
                    return {
                        "status": "success",
                        "success": True,
                        "dialogue_script": dialogue_script,
                        "final_audio_path": final_audio_path,
                        "summary_count": len(summaries) if isinstance(summaries, list) else 0,
                        "transcript_count": len(transcripts) if isinstance(transcripts, dict) else 0,
                        "failed_transcripts": [],
                        "error": None
                    }
                else:
                    return self._error_result(
                        "ADK pipeline completed but no audio file was generated", 
                        video_ids
                    )
                    
        except Exception as e:
            logger.exception(f"ADK Pipeline error: {e}")
            return self._error_result(f"ADK Pipeline error: {e}", video_ids)
        
        finally:
            # Clean up temporary directories
            self._cleanup()
    
    def _error_result(self, error_msg: str, video_ids: List[str]) -> Dict[str, Any]:
        """
        Create standardized error result dictionary.
        
        Args:
            error_msg: Error message to include
            video_ids: Video IDs that failed processing
            
        Returns:
            Standardized error result dictionary
        """
        return {
            "status": "error",
            "success": False,
            "dialogue_script": [],
            "final_audio_path": None,
            "summary_count": 0,
            "transcript_count": 0,
            "failed_transcripts": video_ids,
            "error": error_msg
        }
    
    def _cleanup(self):
        """Clean up temporary directories and resources."""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory {temp_dir}: {e}")
        
        self.temp_dirs.clear()
    
    def run_pipeline(self, video_ids: List[str], output_dir: str = "./output_audio") -> Dict[str, Any]:
        """
        Synchronous wrapper for the async ADK pipeline.
        
        Args:
            video_ids: List of YouTube video IDs to process
            output_dir: Directory for final audio output
            
        Returns:
            Pipeline execution results
        """
        logger.info("Running ADK pipeline synchronously")
        
        # For sync execution, use asyncio.run
        return asyncio.run(self.run_async(video_ids, output_dir))

# Advanced ADK Runner with Parallel Processing
class AdvancedAdkPipelineRunner(AdkPipelineRunner):
    """
    Advanced ADK pipeline runner with parallel processing capabilities.
    """
    
    async def run_parallel_async(
        self, 
        video_ids: List[str], 
        output_dir: str,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Run pipeline with parallel processing for multiple videos.
        
        Args:
            video_ids: List of YouTube video IDs to process
            output_dir: Directory for final audio output
            max_concurrent: Maximum number of concurrent processes
            
        Returns:
            Pipeline execution results
        """
        logger.info(f"Starting parallel ADK pipeline for {len(video_ids)} videos")
        
        # Split video IDs into batches for parallel processing
        batches = [
            video_ids[i:i + max_concurrent] 
            for i in range(0, len(video_ids), max_concurrent)
        ]
        
        all_results = []
        
        for batch in batches:
            # Process each batch in parallel
            batch_tasks = [
                self.run_async([video_id], output_dir) 
                for video_id in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            all_results.extend(batch_results)
        
        # Combine results
        successful_results = [r for r in all_results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in all_results if not isinstance(r, dict) or not r.get("success")]
        
        return {
            "status": "completed",
            "success": len(successful_results) > 0,
            "total_processed": len(video_ids),
            "successful_count": len(successful_results),
            "failed_count": len(failed_results),
            "results": all_results
        }