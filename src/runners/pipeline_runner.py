"""
Pipeline Runner for orchestrating the podcast digest generation process.
"""
import logging
import json
from typing import List, Dict, Tuple

# Import agent classes using absolute path from src
from src.agents.transcript_fetcher import TranscriptFetcher
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.audio_generator import AudioGenerator

# Import the actual transcript fetching tool using absolute path from src
from src.tools.transcript_tools import fetch_transcripts
# Import audio tools
from src.tools.audio_tools import generate_audio_segment_tool, combine_audio_segments_tool # Added import

# Import types for agent interaction (even if simulated for now)
from google.genai import types as genai_types
# Added imports for audio processing
import os 
import tempfile
import shutil
from google.cloud import texttospeech

logger = logging.getLogger(__name__)

class PipelineRunner:
    """Orchestrates the sequence of agent calls for podcast digest generation."""

    def __init__(
        self,
        transcript_fetcher: TranscriptFetcher, # Keep agents for potential future use with ADK Runner
        summarizer: SummarizerAgent,
        synthesizer: SynthesizerAgent,
        audio_generator: AudioGenerator
    ):
        """Initialize the PipelineRunner with the required agents."""
        self.transcript_fetcher = transcript_fetcher
        self.summarizer = summarizer
        self.synthesizer = synthesizer
        self.audio_generator = audio_generator
        logger.info("PipelineRunner initialized with agents.")

    def _process_transcript_results(self, results: Dict[str, Dict[str, any]]) -> Tuple[Dict[str, str], List[str]]:
        """Separates successful transcripts from failed fetches."""
        transcripts = {}
        failed_fetches = []
        for video_id, result in results.items():
            if result.get("status") == "success":
                transcripts[video_id] = result.get("result", {}).get("transcript", "")
                logger.debug(f"Successfully processed transcript for {video_id}")
            else:
                failed_fetches.append(video_id)
                logger.warning(f"Failed to fetch transcript for {video_id}: {result.get('error')}")
        return transcripts, failed_fetches

    # TODO: Replace simulated agent runs with actual ADK Runner calls or async agent.run() calls
    # TODO: Pass output directory properly
    async def run_pipeline_async(self, video_ids: List[str], output_dir: str = "./output_audio") -> Dict[str, any]:
        """Runs the full pipeline asynchronously from video IDs to dialogue script.

        NOTE: This currently uses direct tool calls and SIMULATED agent runs.
              Replace simulation with actual async agent.run() calls later.

        Args:
            video_ids: A list of YouTube video IDs.
            output_dir: The directory to save the final audio output.

        Returns:
            A dictionary containing the final dialogue script, audio path, or errors.
        """
        logger.info(f"Starting async pipeline for {len(video_ids)} video IDs.")
        final_audio_path = None # Initialize
        temp_segment_dir = None # Initialize
        # Initialize TTS client once if needed by tools
        tts_client = texttospeech.TextToSpeechClient()

        # --- 1. Fetch Transcripts (Direct Tool Call - using .func) ---
        logger.info("Step 1: Fetching transcripts...")
        try:
            # Directly call the underlying function via .func
            fetch_tool_result = fetch_transcripts.func(video_ids=video_ids)
            # The raw function returns the dict directly now
            transcripts, failed_fetches = self._process_transcript_results(fetch_tool_result.get("results", {}))
            logger.info(f"Transcript fetching complete. Success: {len(transcripts)}, Failures: {len(failed_fetches)}.")
        except Exception as e:
            logger.exception("Error during transcript fetching tool call.")
            transcripts = {}
            failed_fetches = video_ids

        # --- 2. Summarize Transcripts (Simulated Agent Run) ---
        logger.info("Step 2: Summarizing transcripts...")
        summaries = []
        if not transcripts:
            logger.warning("No transcripts available to summarize.")
        else:
            for video_id, transcript_text in transcripts.items():
                logger.debug(f"Preparing summarization for {video_id}...")
                if not transcript_text:
                    logger.warning(f"Skipping summarization for {video_id} due to empty transcript.")
                    continue
                
                # Prepare input for the SummarizerAgent (as if calling agent.run)
                # summary_content_input = genai_types.Content(role='user', parts=[genai_types.Part(text=transcript_text)])
                logger.info(f"[SIMULATED] Calling SummarizerAgent for {video_id}...")
                # --- Replace below with actual async call: --- 
                # try:
                #     async for event in self.summarizer.run(content=summary_content_input):
                #         if event.event_type == genai_types.EventType.AGENT_TEXT:
                #             summary = event.text
                #             summaries.append(summary)
                #             logger.debug(f"Received summary for {video_id}")
                #             break # Assuming one summary per run
                # except Exception as e:
                #     logger.error(f"Error summarizing {video_id}: {e}")
                # ---------------------------------------------
                summary = f"This is a simulated summary for video {video_id} based on its transcript." # Dummy data
                summaries.append(summary)
                logger.debug(f"[SIMULATED] Received summary for {video_id}")

            logger.info(f"Summarization step complete. Generated {len(summaries)} summaries.")

        # --- 3. Synthesize Dialogue (Simulated Agent Run) ---
        logger.info("Step 3: Synthesizing dialogue...")
        dialogue_script = []
        if not summaries:
            logger.warning("No summaries available to synthesize dialogue.")
        else:
            try:
                # Prepare input for the SynthesizerAgent
                summaries_json = json.dumps(summaries)
                # synthesis_content_input = genai_types.Content(role='user', parts=[genai_types.Part(text=summaries_json)])
                logger.info("[SIMULATED] Calling SynthesizerAgent...")
                # --- Replace below with actual async call: --- 
                # dialogue_script_json = None
                # async for event in self.synthesizer.run(content=synthesis_content_input):
                #     if event.event_type == genai_types.EventType.AGENT_TEXT:
                #         dialogue_script_json = event.text
                #         logger.debug("Received synthesized script text.")
                #         break # Assuming one script output per run
                #
                # if dialogue_script_json:
                #     try:
                #         dialogue_script = json.loads(dialogue_script_json)
                #         if not isinstance(dialogue_script, list):
                #             raise ValueError("Synthesized output is not a list")
                #         logger.info("Successfully parsed synthesized dialogue script.")
                #     except (json.JSONDecodeError, ValueError) as json_e:
                #         logger.error(f"Failed to parse JSON output from SynthesizerAgent: {json_e}")
                #         logger.error(f"Received text: {dialogue_script_json}")
                #         dialogue_script = [] # Failed to parse
                # else:
                #     logger.error("SynthesizerAgent did not return text output.")
                # ---------------------------------------------
                dialogue_script = [ # Dummy data
                    {"speaker": "A", "line": "Hello, this is a simulated dialogue based on summaries."}, 
                    {"speaker": "B", "line": f"Indeed, covering {len(summaries)} points."}
                ]
                logger.info("[SIMULATED] Successfully processed synthesized dialogue script.")

            except Exception as e:
                logger.exception("Error during dialogue synthesis step.")
                dialogue_script = []

        # --- 4. Generate Audio Segments --- 
        logger.info("Step 4: Generating audio segments...")
        segment_files = []
        if not dialogue_script:
            logger.warning("No dialogue script available to generate audio.")
        else:
            try:
                # Create a temporary directory for segments
                # Using tempfile for robustness
                temp_segment_dir = tempfile.mkdtemp(prefix="podcast_segments_")
                logger.info(f"Created temporary directory for audio segments: {temp_segment_dir}")

                for i, segment in enumerate(dialogue_script):
                    line = segment.get("line")
                    speaker = segment.get("speaker")
                    if not line or not speaker:
                        logger.warning(f"Skipping invalid dialogue segment: {segment}")
                        continue
                    
                    segment_filename = f"segment_{i:03d}_{speaker}.mp3"
                    segment_filepath = os.path.join(temp_segment_dir, segment_filename)
                    
                    logger.info(f"[SIMULATED] Calling AudioGenerator tool (generate_audio_segment) for segment {i}...")
                    # --- Replace below with actual async agent/tool call: ---
                    # try:
                    #     # Potential agent call structure:
                    #     # audio_gen_input = types.Content(role='user', parts=[types.Part(text=json.dumps({...}))])
                    #     # async for event in self.audio_generator.run(content=audio_gen_input):
                    #     #     if event.is_final_response(): # Or check for specific tool result
                    #     #         segment_result = event.text # Or parse tool result
                    #     #         if segment_result:
                    #     #            segment_files.append(segment_result)
                    #     #            break
                    #     pass 
                    # except Exception as audio_e:
                    #     logger.error(f"Error during audio generation tool call for segment {i}: {audio_e}")
                    # -----------------------------------------------------------
                    # Direct tool call simulation:
                    segment_result = generate_audio_segment_tool.func(
                        text=line,
                        speaker=speaker,
                        output_filepath=segment_filepath,
                        tts_client=tts_client # Pass initialized client
                    )
                    # -----------------------------------------------------------

                    if segment_result:
                        segment_files.append(segment_result)
                        logger.debug(f"Successfully generated audio segment: {segment_result}")
                    else:
                        logger.error(f"Failed to generate audio segment {i} for speaker {speaker}.")
                        # Decide whether to stop the whole process or continue without this segment
                        # For now, we continue, but the concatenation might fail or be incomplete

                logger.info(f"Audio segment generation step complete. Generated {len(segment_files)} segments.")

            except Exception as e:
                logger.exception("Error during audio segment generation loop.")
                segment_files = [] # Clear segment list on error

        # --- 5. Concatenate Audio Segments --- 
        logger.info("Step 5: Concatenating audio segments...")
        if not segment_files:
            logger.warning("No audio segments available to concatenate.")
        else:
            try:
                logger.info(f"[SIMULATED] Calling AudioGenerator tool (combine_audio_segments)...")
                 # --- Replace below with actual async agent/tool call: ---
                # try:
                #     # Potential agent call structure:
                #     # combine_input = types.Content(role='user', parts=[types.Part(text=json.dumps({...}))])
                #     # async for event in self.audio_generator.run(content=combine_input):
                #     #    # ... process result ... 
                #     pass
                # except Exception as combine_e:
                #      logger.error(f"Error during audio combination tool call: {combine_e}")
                # -----------------------------------------------------------
                # Direct tool call simulation:
                final_audio_path = combine_audio_segments_tool.func(
                    segment_filepaths=segment_files,
                    output_dir=output_dir
                )
                # -----------------------------------------------------------

                if final_audio_path:
                    logger.info(f"Successfully concatenated audio to: {final_audio_path}")
                else:
                    logger.error("Failed to concatenate audio segments.")

            except Exception as e:
                logger.exception("Error during audio concatenation step.")
                final_audio_path = None

        # --- Cleanup --- 
        if temp_segment_dir and os.path.exists(temp_segment_dir):
            try:
                logger.info(f"Cleaning up temporary segment directory: {temp_segment_dir}")
                shutil.rmtree(temp_segment_dir)
            except Exception as e:
                logger.warning(f"Failed to remove temporary directory {temp_segment_dir}: {e}")

        logger.info("Async pipeline finished.")
        return {
            "status": "success" if final_audio_path else "partial_failure", # Adjust status based on audio success
            "dialogue_script": dialogue_script,
            "failed_transcripts": failed_fetches,
            "summary_count": len(summaries),
            "final_audio_path": final_audio_path # Add final audio path
        }
    
    # Keep the synchronous wrapper for now, calling the async version
    # This requires the main script to run asyncio.run()
    def run_pipeline(self, video_ids: List[str]) -> Dict[str, any]:
        import asyncio
        logger.warning("Running pipeline synchronously using asyncio.run(). Consider running the main script asynchronously.")
        try:
            return asyncio.run(self.run_pipeline_async(video_ids))
        except RuntimeError as e:
            logger.error(f"RuntimeError running async pipeline (maybe loop already running?): {e}")
            # Fallback or re-raise depending on desired behavior
            return {"status": "error", "error": str(e), "dialogue_script": [], "failed_transcripts": video_ids, "summary_count": 0}
        except Exception as e:
            logger.exception("Unexpected error running async pipeline wrapper.")
            return {"status": "error", "error": str(e), "dialogue_script": [], "failed_transcripts": video_ids, "summary_count": 0} 