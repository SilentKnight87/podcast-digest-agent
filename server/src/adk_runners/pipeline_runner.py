"""
ADK-based pipeline runner for podcast digest generation.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any

# Suppress expected Google GenAI warnings
logging.getLogger("google_genai.types").setLevel(logging.ERROR)

# ADK will use Vertex AI via environment variables:
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=podcast-digest-agent  
# GOOGLE_CLOUD_LOCATION=us-central1

# ADK imports
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from src.config.settings import settings
from src.core import task_manager

from ..adk_agents.podcast_agent_sequential import root_agent
from .websocket_bridge import AdkWebSocketBridge

logger = logging.getLogger(__name__)


class AdkPipelineRunner:
    """ADK-based pipeline runner."""

    def __init__(self):
        """Initialize ADK runner with services."""
        self.session_service = InMemorySessionService()
        self.artifact_service = InMemoryArtifactService()

        self.runner = Runner(
            agent=root_agent,
            session_service=self.session_service,
            artifact_service=self.artifact_service,
            app_name="podcast_digest_app",
        )

        logger.info("ADK Pipeline Runner initialized")

    async def run_async(
        self, video_ids: list[str], output_dir: str, task_id: str | None = None
    ) -> dict[str, Any]:
        """Run the complete pipeline using ADK with WebSocket support.

        Args:
            video_ids: List of YouTube video IDs to process
            output_dir: Directory for final audio output
            task_id: Optional task ID for WebSocket updates

        Returns:
            Dictionary containing results and status information
        """
        logger.info(f"Starting ADK pipeline for {len(video_ids)} videos")

        # Add timeout handling
        import asyncio

        try:
            # Run with a timeout of 5 minutes
            return await asyncio.wait_for(
                self._run_pipeline_internal(video_ids, output_dir, task_id),
                timeout=300.0,  # 5 minutes
            )
        except TimeoutError:
            error_msg = "Pipeline timed out after 5 minutes"
            logger.error(error_msg)
            if task_id:
                task_manager.set_task_failed(task_id, error_msg)
            return self._error_result(error_msg, video_ids)

    async def _run_pipeline_internal(
        self, video_ids: list[str], output_dir: str, task_id: str | None = None
    ) -> dict[str, Any]:
        """Internal pipeline execution method."""
        logger.info(f"Running internal pipeline for {len(video_ids)} videos")

        # Initialize WebSocket bridge if task_id provided
        ws_bridge = None
        if task_id:
            ws_bridge = AdkWebSocketBridge(task_id)

            # Set initial agent statuses
            initial_agents = [
                "transcript-fetcher",
                "summarizer-agent",
                "synthesizer-agent",
                "audio-generator",
            ]
            for agent_id in initial_agents:
                task_manager.update_agent_status(
                    task_id=task_id, agent_id=agent_id, new_status="pending", progress=0.0
                )

        try:
            # Ensure output_dir is absolute path
            output_path = Path(output_dir).resolve()
            output_path.mkdir(parents=True, exist_ok=True)

            # Create session
            session = await self.session_service.create_session(
                state={"video_ids": video_ids, "output_dir": str(output_path)},
                app_name="podcast_digest_app",
                user_id="system_user",
            )

            # Prepare input message
            from google.genai.types import Content, Part

            input_message = f"Process YouTube videos with IDs: {video_ids}"
            user_content = Content(role="user", parts=[Part(text=input_message)])

            # Run the agent and process events
            events = []
            logger.info(
                f"Starting ADK runner with session_id={session.id}, user_id={session.user_id}"
            )
            logger.info(f"User message: {user_content}")

            # Add debug logging for runner execution
            logger.info("About to start ADK runner.run_async iteration...")
            event_count = 0

            async for event in self.runner.run_async(
                session_id=session.id, user_id=session.user_id, new_message=user_content
            ):
                event_count += 1
                events.append(event)
                logger.info(f"Received event #{event_count} type: {type(event).__name__}")
                logger.debug(f"Event details: {event}")

                # Send WebSocket updates if bridge is available
                if ws_bridge:
                    await ws_bridge.process_adk_event(event)

                # Yield control back to event loop periodically
                if event_count % 10 == 0:
                    await asyncio.sleep(0.01)

            logger.info(f"ADK runner completed with {event_count} total events")

            # Get the updated session with final state
            updated_session = await self.session_service.get_session(
                app_name="podcast_digest_app", user_id="system_user", session_id=session.id
            )

            # Extract results from updated session state
            session_state = updated_session.state

            # Handle case where state might be a string or dict
            if isinstance(session_state, str):
                logger.warning(f"Session state is a string: {session_state}")
                # Try to parse it as JSON if it's a string
                import json

                try:
                    session_state = json.loads(session_state)
                except:
                    logger.error("Failed to parse session state as JSON")
                    session_state = {}
            elif not isinstance(session_state, dict):
                logger.error(f"Unexpected session state type: {type(session_state)}")
                session_state = {}

            final_audio_path = (
                session_state.get("final_audio_path") if isinstance(session_state, dict) else None
            )
            dialogue_script = (
                session_state.get("dialogue_script", []) if isinstance(session_state, dict) else []
            )
            summaries = (
                session_state.get("summaries", []) if isinstance(session_state, dict) else []
            )

            # Log the raw values for debugging
            logger.info(
                f"Session state keys: {list(session_state.keys()) if isinstance(session_state, dict) else 'Not a dict'}"
            )
            logger.info(f"Raw final_audio_path from state: {repr(final_audio_path)[:200]}...")
            logger.info(f"Type of final_audio_path: {type(final_audio_path)}")

            # Check if final_audio_path contains dialogue script instead of file path
            if isinstance(final_audio_path, str):
                # If it starts with JSON markers, try to extract the actual path
                if final_audio_path.strip().startswith(("```", "[", "{")):
                    logger.warning(
                        "final_audio_path contains JSON wrapper, attempting to extract path..."
                    )
                    try:
                        import json
                        import re

                        # Remove markdown code block markers
                        clean_text = final_audio_path.strip()
                        if clean_text.startswith("```"):
                            lines = clean_text.split("\n")
                            if len(lines) >= 3 and lines[-1].strip() == "```":
                                clean_text = "\n".join(lines[1:-1])

                        # Try to parse as JSON, handling escape sequences
                        # First try to fix common escape issues
                        clean_text = clean_text.replace("\\\\", "\\").replace('\\"', '"')
                        parsed = json.loads(clean_text)
                        if isinstance(parsed, dict) and "final_audio_path" in parsed:
                            extracted_path = parsed["final_audio_path"]
                            if extracted_path and extracted_path.endswith(".mp3"):
                                logger.info(f"Extracted audio path from JSON: {extracted_path}")
                                # Handle relative paths
                                if not extracted_path.startswith("/"):
                                    # Convert relative path to absolute
                                    if extracted_path.startswith("audio/"):
                                        # Replace "audio/" with the actual output directory
                                        filename = extracted_path.replace("audio/", "")
                                        final_audio_path = str(output_path / filename)
                                    else:
                                        final_audio_path = str(output_path / extracted_path)
                                    logger.info(f"Converted to absolute path: {final_audio_path}")
                                else:
                                    final_audio_path = extracted_path
                            else:
                                logger.error("Extracted path is not valid")
                                final_audio_path = None
                        else:
                            logger.error("JSON does not contain final_audio_path field")
                            final_audio_path = None
                    except Exception as e:
                        logger.error(f"Failed to extract path from JSON: {e}")
                        final_audio_path = None
                # Extract actual audio path if it's embedded in text
                elif "saved it to" in final_audio_path:
                    import re

                    # Match the path more precisely, stopping at whitespace or punctuation
                    match = re.search(r"saved it to ([^\s]+\.mp3)", final_audio_path)
                    if match:
                        final_audio_path = match.group(1).strip()
                        # Remove any trailing punctuation or newlines
                        final_audio_path = final_audio_path.rstrip(".\n")
                        logger.info(f"Extracted audio path: {final_audio_path}")
                # Check if it looks like a valid file path
                elif not (
                    final_audio_path.endswith(".mp3")
                    and ("/" in final_audio_path or "\\" in final_audio_path)
                ):
                    logger.warning(
                        f"final_audio_path doesn't look like a valid file path: {final_audio_path[:100]}..."
                    )
                    final_audio_path = None

            # Fallback: If no valid audio path found, look for the most recent audio file
            if not final_audio_path:
                logger.info(
                    "No valid audio path found in session state, searching for recent audio files..."
                )
                import glob
                import os

                # Look for audio files in output directory
                audio_pattern = str(output_path / "podcast_digest_*.mp3")
                audio_files = glob.glob(audio_pattern)

                if audio_files:
                    # Sort by modification time, get the most recent
                    audio_files.sort(key=os.path.getmtime, reverse=True)
                    most_recent = audio_files[0]

                    # Check if this file was created recently (within last 10 minutes)
                    file_age = time.time() - os.path.getmtime(most_recent)
                    if file_age < 600:  # 10 minutes
                        final_audio_path = most_recent
                        logger.info(
                            f"Found recent audio file: {final_audio_path} (age: {file_age:.1f}s)"
                        )
                    else:
                        logger.warning(f"Most recent audio file is too old: {file_age:.1f}s")
                        # As a last resort, check if there are any files from today
                        from datetime import datetime

                        today = datetime.now().strftime("%Y%m%d")
                        today_files = [f for f in audio_files if today in f]
                        if today_files:
                            final_audio_path = today_files[0]  # Use most recent from today
                            logger.info(f"Using most recent file from today: {final_audio_path}")
                else:
                    logger.warning("No audio files found in output directory")

            # Parse dialogue script if it's a JSON string with markdown
            if isinstance(dialogue_script, str):
                import json
                import re

                # Remove markdown code block formatting if present
                dialogue_text = dialogue_script.strip()
                if dialogue_text.startswith("```"):
                    # Simple approach: remove first line and last line
                    lines = dialogue_text.split("\n")
                    if len(lines) >= 3 and lines[-1].strip() == "```":
                        # Remove first line (```json or ```) and last line (```)
                        dialogue_text = "\n".join(lines[1:-1])
                try:
                    dialogue_script = json.loads(dialogue_text)
                except Exception as e:
                    logger.warning(f"Failed to parse dialogue script JSON: {e}")
                    dialogue_script = []

            if final_audio_path:
                try:
                    # Copy audio file to output directory if needed
                    final_path = Path(final_audio_path)
                    logger.info(f"Checking audio file at: {final_path}")

                    if final_path.exists():
                        if str(output_path) not in str(final_path):
                            # Copy file to the correct output directory
                            import shutil

                            dest_path = output_path / final_path.name
                            logger.info(f"Copying from {final_path} to {dest_path}")
                            shutil.copy2(final_path, dest_path)
                            final_audio_path = str(dest_path)
                            logger.info(f"Copied audio to output directory: {final_audio_path}")
                        else:
                            logger.info(
                                f"Audio file already in output directory: {final_audio_path}"
                            )
                    else:
                        logger.warning(f"Audio file not found at: {final_path}")
                except Exception as e:
                    logger.error(f"Error processing audio file path: {e}")
                    logger.error(f"Invalid audio path: {repr(final_audio_path)[:200]}")
                    final_audio_path = None

                # Mark final data flow and task as completed
                if task_id and final_audio_path:
                    # Ensure all agents are marked as completed
                    task_manager.update_agent_status(
                        task_id=task_id,
                        agent_id="transcript-fetcher",
                        new_status="completed",
                        progress=100,
                    )
                    task_manager.update_agent_status(
                        task_id=task_id,
                        agent_id="summarizer-agent",
                        new_status="completed",
                        progress=100,
                    )
                    task_manager.update_agent_status(
                        task_id=task_id,
                        agent_id="synthesizer-agent",
                        new_status="completed",
                        progress=100,
                    )
                    task_manager.update_agent_status(
                        task_id=task_id,
                        agent_id="audio-generator",
                        new_status="completed",
                        progress=100,
                    )
                    task_manager.update_agent_status(
                        task_id=task_id, agent_id="ui-player", new_status="completed", progress=100
                    )

                    # Mark all data flows as completed
                    task_manager.update_data_flow_status(
                        task_id, "youtube-node", "transcript-fetcher", "completed"
                    )
                    task_manager.update_data_flow_status(
                        task_id, "transcript-fetcher", "summarizer-agent", "completed"
                    )
                    task_manager.update_data_flow_status(
                        task_id, "summarizer-agent", "synthesizer-agent", "completed"
                    )
                    task_manager.update_data_flow_status(
                        task_id, "synthesizer-agent", "audio-generator", "completed"
                    )
                    task_manager.update_data_flow_status(
                        task_id, "audio-generator", "ui-player", "completed"
                    )

                    # Extract summary from dialogue
                    summary_text = self._create_summary_from_dialogue(dialogue_script)

                    # Create audio URL
                    audio_filename = Path(final_audio_path).name
                    audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}"

                    # Mark task completed
                    task_manager.set_task_completed(task_id, summary_text, audio_url)

                    logger.info(f"Pipeline completed successfully for task {task_id}")
                    logger.info(f"Audio file: {final_audio_path}")
                    logger.info(f"Summary length: {len(summary_text) if summary_text else 0}")
                    logger.info(f"Audio URL: {audio_url}")

                return {
                    "status": "success",
                    "success": True,
                    "final_audio_path": final_audio_path,
                    "dialogue_script": dialogue_script,
                    "summary_count": len(summaries) if isinstance(summaries, list) else 0,
                    "transcript_count": len(video_ids),
                    "failed_transcripts": [],
                    "error": None,
                }
            else:
                error_msg = "Pipeline completed but no audio file was generated"
                logger.error(error_msg)
                if task_id:
                    # Mark task as failed and update all agent statuses
                    task_manager.set_task_failed(task_id, error_msg)
                    # Mark current agent as failed if we know which one it was
                    task_manager.update_agent_status(
                        task_id=task_id,
                        agent_id="audio-generator",  # Most likely failure point
                        new_status="error",
                        progress=0,
                    )
                return self._error_result(error_msg, video_ids)

        except Exception as e:
            logger.exception(f"ADK Pipeline error: {e}")
            if task_id:
                task_manager.set_task_failed(task_id, f"Pipeline error: {e}")
            return self._error_result(f"Pipeline error: {e}", video_ids)

    def _error_result(self, error_msg: str, video_ids: list[str]) -> dict[str, Any]:
        """Create standardized error result."""
        return {
            "status": "error",
            "success": False,
            "final_audio_path": None,
            "dialogue_script": [],
            "summary_count": 0,
            "transcript_count": 0,
            "failed_transcripts": video_ids,
            "error": error_msg,
        }

    def run_pipeline(
        self, video_ids: list[str], output_dir: str = "./output_audio"
    ) -> dict[str, Any]:
        """Synchronous wrapper for the async pipeline."""
        import asyncio

        return asyncio.run(self.run_async(video_ids, output_dir))

    def _create_summary_from_dialogue(self, dialogue_script) -> str:
        """Create summary text from dialogue script."""
        if not dialogue_script:
            return "ADK Generated Summary"

        # Handle case where dialogue_script is not a list
        if not isinstance(dialogue_script, list):
            return "ADK Generated Summary"

        summary_lines = []
        # Safely take first 3 items
        items_to_process = dialogue_script[:3] if len(dialogue_script) >= 3 else dialogue_script

        for item in items_to_process:
            if isinstance(item, dict):
                speaker = item.get("speaker", "")
                line = item.get("line", "")
                if line:
                    summary_lines.append(f"{speaker}: {line}")
            elif isinstance(item, str):
                # Handle case where dialogue_script contains strings
                summary_lines.append(item)

        return (
            "ADK Generated Summary: " + " | ".join(summary_lines)
            if summary_lines
            else "ADK Generated Summary"
        )
