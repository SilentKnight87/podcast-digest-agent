import asyncio
from datetime import datetime, timezone
from pathlib import Path
import logging
import json
import shutil
import subprocess

from src.config.settings import settings
from src.models.api_models import ProcessUrlRequest
from src.core import task_manager
from src.utils.audio_placeholder import create_silent_audio
from src.agents.synthesizer import SynthesizerAgent
from src.agents.audio_generator import AudioGenerator
from src.agents.base_agent import BaseAgentEventType
from src.utils.create_test_audio import create_test_wav

logger = logging.getLogger(__name__)

async def run_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """
    Process a YouTube URL through the pipeline of agents.
    This is run as a background task after the API request is accepted.
    
    This function now uses the URL directly from the API request rather than
    reading from the input/youtube_links.txt file.
    """
    # Extract YouTube URL from request data
    youtube_url = request_data.youtube_url
    logger.info(f"Processing YouTube URL: {youtube_url}, task ID: {task_id}")
    
    try:
        # Update status to processing
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=5, 
            current_agent_id="youtube-node"
        )
        
        # For simulation, we'll assume a YouTube source processing step
        await asyncio.sleep(2)  # simulate some processing time
        logger.info(f"Starting YouTube source processing for task {task_id}")
        
        # Update YouTube source status
        task_manager.update_agent_status(
            task_id, 
            "youtube-node", 
            "running", 
            progress=50,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Add some sample logs to the YouTube source agent
        task_manager.add_agent_log(
            task_id, 
            "youtube-node", 
            "INFO", 
            f"Processing YouTube URL directly from API request: {youtube_url}"
        )
        
        # Complete the YouTube source processing
        await asyncio.sleep(2)
        task_manager.update_agent_status(
            task_id, 
            "youtube-node", 
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
            "youtube-node", 
            "transcript-fetcher", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "youtube-node", 
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
        
        # Placeholder for actual summary retrieval
        # In a real implementation, this would be the output of the SummarizerAgent
        # TODO: Replace this with actual transcript fetching and summarization
        summary = f"This is a dynamic summary for the YouTube video: {youtube_url}. This video discusses various topics that would normally be extracted from the actual transcript. Key points would include the main themes, important discussions, and conclusions from the content. This system is currently in development mode and will be replaced with real transcript processing and AI summarization."
        task_manager.add_agent_log(
            task_id,
            "summarizer-agent",
            "INFO",
            f"Summary generated: {summary[:100]}..."
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
        
        # Create a real audio file using the AudioGenerator agent
        audio_filename = f"{task_id}_digest.mp3"  # Changed to MP3 format for better compatibility
        output_audio_dir = Path(settings.OUTPUT_AUDIO_DIR)
        output_audio_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        
        try:
            # Import the AudioGenerator agent
            from src.agents.audio_generator import AudioGenerator
            
            # Initialize the AudioGenerator agent
            audio_generator = AudioGenerator()
            
            # Use the SynthesizerAgent to create a dialogue script from the summary
            try:
                from src.agents.synthesizer import SynthesizerAgent
                
                # Initialize the SynthesizerAgent
                synthesizer_agent = SynthesizerAgent()
                
                # Prepare the summary for the synthesizer
                # The synthesizer expects a JSON list of strings, so we'll put our summary in a list
                summary_json = json.dumps([summary])
                
                # Use the synthesizer to generate a dialogue script
                logger.info(f"Using SynthesizerAgent to create dialogue script for task {task_id}")
                
                # Process the events from the generator
                dialogue_script = []
                async for event in synthesizer_agent.run_async(summary_json):
                    if event.type == BaseAgentEventType.RESULT:
                        # Extract the dialogue from the result
                        dialogue_script = event.payload.get('dialogue', [])
                        logger.info(f"Successfully generated dialogue script with {len(dialogue_script)} lines")
                        break  # Exit the loop once we get the result
                    elif event.type == BaseAgentEventType.ERROR:
                        # Log any errors from the synthesizer
                        error_message = event.payload.get('error', 'Unknown error')
                        logger.error(f"Error generating dialogue script: {error_message}")
                        break  # Exit the loop on error
                
                # If the dialogue script is empty or there was an error, use a fallback script
                if not dialogue_script:
                    logger.warning("Using fallback dialogue script due to empty result from synthesizer")
                    dialogue_script = [
                        {"speaker": "A", "text": "Hello and welcome to today's podcast digest."},
                        {"speaker": "B", "text": "We're going to summarize the main points from the content you've requested."},
                        {"speaker": "A", "text": f"Here's what we found: {summary[:150]}..."},  # First part of summary
                        {"speaker": "B", "text": f"Additionally, {summary[150:300]}..." if len(summary) > 150 else "That covers the main points."},  # Second part of summary
                        {"speaker": "A", "text": f"To conclude, {summary[300:450]}..." if len(summary) > 300 else "That's our summary for today."},  # Third part of summary
                        {"speaker": "B", "text": "Thanks for listening to this podcast digest."}
                    ]
                
                # Transform the dialogue format if needed
                # SynthesizerAgent uses {'speaker': X, 'line': Y} format, 
                # but AudioGenerator expects {'speaker': X, 'text': Y}
                formatted_dialogue_script = []
                for item in dialogue_script:
                    if 'speaker' in item and ('line' in item or 'text' in item):
                        formatted_item = {"speaker": item['speaker']}
                        # Use either 'line' or 'text' key, preferring 'text' if both exist
                        formatted_item['text'] = item.get('text', item.get('line', ''))
                        formatted_dialogue_script.append(formatted_item)
                
                dialogue_script = formatted_dialogue_script
                
            except Exception as e:
                logger.exception(f"Failed to run synthesizer agent: {e}")
                # Use fallback dialogue script
                logger.warning("Using fallback dialogue script due to exception in synthesizer")
                dialogue_script = [
                    {"speaker": "A", "text": "Hello and welcome to today's podcast digest."},
                    {"speaker": "B", "text": "We're going to summarize the main points from the content you've requested."},
                    {"speaker": "A", "text": f"Here's what we found: {summary[:150]}..."},  # First part of summary
                    {"speaker": "B", "text": f"Additionally, {summary[150:300]}..." if len(summary) > 150 else "That covers the main points."},  # Second part of summary
                    {"speaker": "A", "text": f"To conclude, {summary[300:450]}..." if len(summary) > 300 else "That's our summary for today."},  # Third part of summary
                    {"speaker": "B", "text": "Thanks for listening to this podcast digest."}
                ]
            
            # Convert dialogue script to JSON
            script_json = json.dumps({
                "script": dialogue_script,
                "output_dir": str(output_audio_dir)
            })
            
            # Run the audio generator agent
            logger.info(f"Running AudioGenerator agent for task {task_id}")
            result = await audio_generator.run(script_json)
            
            # Check if the audio generation was successful
            if isinstance(result, dict) and "response" in result and "error" not in result:
                final_audio_path = result.get("response")
                
                # If the response contains a file path, extract the filename
                if isinstance(final_audio_path, str) and "Successfully generated the final audio file at:" in final_audio_path:
                    # Extract the file path from the response
                    import re
                    path_match = re.search(r'at:\s*(.+?)(?:\s|$)', final_audio_path)
                    if path_match:
                        extracted_path = path_match.group(1)
                        # Get just the filename for the URL
                        audio_filename = Path(extracted_path).name
                        logger.info(f"Successfully generated audio file: {extracted_path}")
                        # Store the full file path for later use
                        audio_file_path = Path(extracted_path)
                    else:
                        logger.warning(f"Could not extract path from audio generator response: {final_audio_path}")
                else:
                    logger.warning(f"Unexpected response format from audio generator: {final_audio_path}")
            else:
                # If there was an error, log it and fall back to placeholder audio
                error_message = result.get("error", "Unknown error") if isinstance(result, dict) else "Unknown error format"
                logger.error(f"Error generating audio: {error_message}")
                
                # Fall back to test audio if real generation fails
                from src.utils.create_test_audio import create_test_wav
                audio_file_path = output_audio_dir / audio_filename
                create_test_wav(str(audio_file_path), duration_seconds=10.0)
                logger.info(f"Created fallback audio file: {audio_file_path} after generation error")
        except Exception as e:
            logger.exception(f"Failed to run audio generator: {e}")
            
            # Fall back to test audio as a last resort
            try:
                # Ensure we have a consistent file extension
                if audio_filename.endswith('.wav'):
                    from src.utils.create_test_audio import create_test_wav
                    audio_file_path = output_audio_dir / audio_filename
                    create_test_wav(str(audio_file_path), duration_seconds=10.0)
                    logger.info(f"Created fallback WAV audio file: {audio_file_path} after exception")
                else:
                    # For mp3 or other formats, use a more consistent approach
                    # First create a WAV file using our utility
                    from src.utils.create_test_audio import create_test_wav
                    temp_wav_path = output_audio_dir / f"{task_id}_temp.wav"
                    create_test_wav(str(temp_wav_path), duration_seconds=10.0)
                    
                    # Then convert it to the desired format if possible (using ffmpeg via subprocess)
                    audio_file_path = output_audio_dir / audio_filename
                    logger.info(f"Converting fallback audio to desired format: {audio_file_path}")
                    
                    try:
                        import subprocess
                        result = subprocess.run(
                            ["ffmpeg", "-i", str(temp_wav_path), "-y", str(audio_file_path)],
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        logger.info(f"Successfully converted audio: {result.stdout}")
                        # Remove temporary file
                        temp_wav_path.unlink(missing_ok=True)
                    except Exception as convert_error:
                        logger.error(f"Error converting audio format: {convert_error}")
                        # If conversion fails, just copy and rename
                        import shutil
                        shutil.copy2(temp_wav_path, audio_file_path)
                        temp_wav_path.unlink(missing_ok=True)
                        logger.info(f"Used WAV file as fallback after conversion failure: {audio_file_path}")
            except Exception as fallback_error:
                logger.error(f"Failed creating fallback audio: {fallback_error}")
                # Create an absolute minimal WAV/MP3 file as a final fallback
                audio_file_path = output_audio_dir / audio_filename
                try:
                    with open(audio_file_path, 'wb') as f:
                        if audio_filename.endswith('.wav'):
                            # Minimal valid WAV header (RIFF + WAVEfmt)
                            f.write(b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00')
                        else:
                            # Minimal empty MP3 file
                            f.write(b'\xFF\xFB\x90\x44\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                    logger.info(f"Created minimal audio file as final fallback: {audio_file_path}")
                except Exception as minimal_error:
                    logger.error(f"Failed even creating minimal audio file: {minimal_error}")
                    # At this point, we just need to ensure audio_file_path is defined
                    # even if the file doesn't actually exist
                    audio_file_path = output_audio_dir / audio_filename
        
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
            current_agent_id="ui-player"
        )
        
        # Update the data flow from audio generator to output player
        task_manager.update_data_flow_status(
            task_id, 
            "audio-generator", 
            "ui-player", 
            "transferring"
        )
        await asyncio.sleep(1)
        task_manager.update_data_flow_status(
            task_id, 
            "audio-generator", 
            "ui-player", 
            "completed"
        )
        
        # Start the output player agent
        task_manager.update_agent_status(
            task_id, 
            "ui-player", 
            "running", 
            progress=50,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Complete output player
        await asyncio.sleep(1)
        task_manager.update_agent_status(
            task_id, 
            "ui-player", 
            "completed", 
            progress=100,
            end_time=datetime.now(timezone.utc).isoformat()
        )
        
        # Construct the URL for the audio file
        # Make sure we use the correct filename
        if not audio_filename:
            logger.warning(f"Audio filename is empty, using default: {task_id}_digest.mp3")
            audio_filename = f"{task_id}_digest.mp3"
            
        # Ensure the audio file exists
        output_audio_dir = Path(settings.OUTPUT_AUDIO_DIR)
        output_audio_dir.mkdir(parents=True, exist_ok=True)
        expected_audio_path = output_audio_dir / audio_filename
        
        if not expected_audio_path.exists():
            logger.warning(f"Expected audio file not found at {expected_audio_path}, checking alternatives")
            
            # Check if audio_file_path was properly set
            if 'audio_file_path' in locals() and audio_file_path.exists():
                logger.info(f"Using existing audio file path: {audio_file_path}")
                # Copy or rename if needed to ensure consistent location
                if audio_file_path.resolve() != expected_audio_path.resolve():
                    import shutil
                    shutil.copy2(audio_file_path, expected_audio_path)
                    logger.info(f"Copied audio from {audio_file_path} to {expected_audio_path}")
        
        # Create the URL with proper format
        audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}"
        logger.info(f"Final audio URL for task {task_id}: {audio_url}")
        
        # Mark the task as completed
        task_manager.set_task_completed(task_id, summary, audio_url)
        logger.info(f"Background task {task_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error in background task {task_id}: {e}", exc_info=True)
        
        # Get more detailed error information
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Detailed error traceback for task {task_id}:\n{error_details}")
        
        # Determine which agent was active when the error occurred
        active_agent_id = None
        try:
            task_status = task_manager.get_task_status(task_id)
            if task_status and task_status.processing_status.current_agent_id:
                active_agent_id = task_status.processing_status.current_agent_id
                
                # Also update the agent status to error
                task_manager.update_agent_status(
                    task_id,
                    active_agent_id,
                    "error",
                    progress=task_status.processing_status.overall_progress
                )
                
                # Add a log to the agent
                task_manager.add_agent_log(
                    task_id,
                    active_agent_id,
                    "ERROR",
                    f"Error during processing: {str(e)}"
                )
        except Exception as agent_error:
            logger.error(f"Additional error while handling the original error for task {task_id}: {agent_error}")
        
        # Create a user-friendly error message
        user_message = f"An error occurred during processing: {str(e)}"
        if active_agent_id:
            agent_name = active_agent_id.replace("-", " ").title()
            user_message = f"Error in {agent_name}: {str(e)}"
        
        # Set the task as failed with the enhanced error message
        task_manager.set_task_failed(task_id, user_message) 