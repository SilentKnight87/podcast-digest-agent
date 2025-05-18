import asyncio
from datetime import datetime, timezone
from pathlib import Path
import logging

from src.config.settings import settings
from src.models.api_models import ProcessUrlRequest
from src.core import task_manager

logger = logging.getLogger(__name__)

async def run_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """
    Process a YouTube URL through the pipeline of agents.
    This is run as a background task after the API request is accepted.
    
    In a production implementation, this would use actual agents and processing.
    For now, it simulates the processing steps with delays.
    """
    logger.info(f"Background task started for {task_id}")
    try:
        # Update status to processing
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=5, 
            current_agent_id="youtube-source"
        )
        
        # For simulation, we'll assume a YouTube source processing step
        await asyncio.sleep(2)  # simulate some processing time
        logger.info(f"Starting YouTube source processing for task {task_id}")
        
        # Update YouTube source status
        task_manager.update_agent_status(
            task_id, 
            "youtube-source", 
            "running", 
            progress=50,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Add some sample logs to the YouTube source agent
        task_manager.add_agent_log(
            task_id, 
            "youtube-source", 
            "INFO", 
            f"Validated YouTube URL: {request_data.youtube_url}"
        )
        
        # Complete the YouTube source processing
        await asyncio.sleep(2)
        task_manager.update_agent_status(
            task_id, 
            "youtube-source", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Start the transcript fetcher agent
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=15, 
            current_agent_id="transcript-fetcher"
        )
        
        # Update the data flow from YouTube source to transcript fetcher
        task_manager.update_data_flow_status(
            task_id, 
            "youtube-source", 
            "transcript-fetcher", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "youtube-source", 
            "transcript-fetcher", 
            "completed"
        )
        
        # Start the transcript fetcher
        task_manager.update_agent_status(
            task_id, 
            "transcript-fetcher", 
            "running", 
            progress=0,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Simulate transcript fetching work
        for i in range(1, 11):
            await asyncio.sleep(0.5)
            task_manager.update_agent_status(
                task_id, 
                "transcript-fetcher", 
                "running", 
                progress=i * 10
            )
            task_manager.add_agent_log(
                task_id, 
                "transcript-fetcher", 
                "INFO", 
                f"Fetching transcript segments: {i * 10}% complete"
            )
        
        # Complete transcript fetching
        task_manager.update_agent_status(
            task_id, 
            "transcript-fetcher", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Move to summarization
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=30, 
            current_agent_id="summarizer-agent"
        )
        
        # Update the data flow from transcript fetcher to summarizer
        task_manager.update_data_flow_status(
            task_id, 
            "transcript-fetcher", 
            "summarizer-agent", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "transcript-fetcher", 
            "summarizer-agent", 
            "completed"
        )
        
        # Start the summarizer
        task_manager.update_agent_status(
            task_id, 
            "summarizer-agent", 
            "running", 
            progress=0,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Simulate summarization work
        for i in range(1, 11):
            await asyncio.sleep(0.7)
            task_manager.update_agent_status(
                task_id, 
                "summarizer-agent", 
                "running", 
                progress=i * 10
            )
            task_manager.add_agent_log(
                task_id, 
                "summarizer-agent", 
                "INFO", 
                f"Summarizing content: {i * 10}% complete"
            )
        
        # Complete summarization
        task_manager.update_agent_status(
            task_id, 
            "summarizer-agent", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Move to synthesis
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=50, 
            current_agent_id="synthesizer-agent"
        )
        
        # Update the data flow from summarizer to synthesizer
        task_manager.update_data_flow_status(
            task_id, 
            "summarizer-agent", 
            "synthesizer-agent", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "summarizer-agent", 
            "synthesizer-agent", 
            "completed"
        )
        
        # Start the synthesizer
        task_manager.update_agent_status(
            task_id, 
            "synthesizer-agent", 
            "running", 
            progress=0,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Simulate synthesis work
        for i in range(1, 6):
            await asyncio.sleep(0.5)
            task_manager.update_agent_status(
                task_id, 
                "synthesizer-agent", 
                "running", 
                progress=i * 20
            )
            task_manager.add_agent_log(
                task_id, 
                "synthesizer-agent", 
                "INFO", 
                f"Synthesizing dialogue: {i * 20}% complete"
            )
        
        # Complete synthesis
        task_manager.update_agent_status(
            task_id, 
            "synthesizer-agent", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Move to audio generation
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=70, 
            current_agent_id="audio-generator"
        )
        
        # Update the data flow from synthesizer to audio generator
        task_manager.update_data_flow_status(
            task_id, 
            "synthesizer-agent", 
            "audio-generator", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "synthesizer-agent", 
            "audio-generator", 
            "completed"
        )
        
        # Start the audio generator
        task_manager.update_agent_status(
            task_id, 
            "audio-generator", 
            "running", 
            progress=0,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Simulate audio generation work
        for i in range(1, 11):
            await asyncio.sleep(0.6)
            task_manager.update_agent_status(
                task_id, 
                "audio-generator", 
                "running", 
                progress=i * 10
            )
            task_manager.add_agent_log(
                task_id, 
                "audio-generator", 
                "INFO", 
                f"Generating audio: {i * 10}% complete"
            )
        
        # Simulate creating an audio file
        audio_filename = f"{task_id}_digest.mp3"
        # Ensure OUTPUT_AUDIO_DIR is correctly referenced via settings
        audio_file_path = Path(settings.OUTPUT_AUDIO_DIR) / audio_filename
        audio_file_path.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
        with open(audio_file_path, "w") as f:  # Create a dummy file
            f.write("This is a dummy audio file.")
        
        # Complete audio generation
        task_manager.update_agent_status(
            task_id, 
            "audio-generator", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Move to output player
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=90, 
            current_agent_id="output-player"
        )
        
        # Update the data flow from audio generator to output player
        task_manager.update_data_flow_status(
            task_id, 
            "audio-generator", 
            "output-player", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "audio-generator", 
            "output-player", 
            "completed"
        )
        
        # Start the output player agent
        task_manager.update_agent_status(
            task_id, 
            "output-player", 
            "running", 
            progress=50,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Complete output player
        await asyncio.sleep(1)
        task_manager.update_agent_status(
            task_id, 
            "output-player", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Construct the URL for the audio file
        audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}" # Ensure API_V1_STR is via settings
        
        # Mark the task as completed
        summary = "In this video, the presenter discusses the key features of the new product " + \
                 "including improved performance, enhanced security, and better user experience. " + \
                 "The product will be available starting next month with a promotional discount " + \
                 "for early adopters. Reviews from beta testers have been overwhelmingly positive."
                 
        task_manager.set_task_completed(task_id, summary, audio_url)
        logger.info(f"Background task {task_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error in background task {task_id}: {e}", exc_info=True)
        task_manager.set_task_failed(task_id, str(e)) 