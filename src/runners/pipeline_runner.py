"""
Pipeline Runner for orchestrating the podcast digest generation process.
"""
import logging
import json
from typing import List, Dict, Tuple
import asyncio
import os
import tempfile
import shutil
from google.cloud import texttospeech

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
import google.generativeai as genai
# InvocationContext removed as it's not used in the simplified agent call
# from google.adk.agents import InvocationContext 
from google.adk.events import Event

logger = logging.getLogger(__name__)

# --- Placeholder Summarizer/Synthesizer logic ---
# Removed simulate_summarizer

# TODO: Remove simulate_synthesizer once agent call is integrated
async def simulate_synthesizer(summaries: List[str]) -> List[Dict[str, str]]:
    logger.info("[SIMULATED] Synthesizer running...")
    await asyncio.sleep(0.01) # Simulate async work
    # Simple alternating dialogue
    dialogue = []
    for i, summary in enumerate(summaries):
        speaker = "A" if i % 2 == 0 else "B"
        dialogue.append({"speaker": speaker, "line": f"Dialogue based on: {summary[:30]}..."})
    return dialogue

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
        self._temp_dirs = []  # Track temporary directories for cleanup
        logger.info("PipelineRunner initialized with agents.")

    def cleanup(self):
        """Clean up any temporary resources created during pipeline execution."""
        logger.info("Cleaning up pipeline resources...")
        for temp_dir in self._temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    logger.info(f"Cleaning up temporary directory: {temp_dir}")
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary directory {temp_dir}: {e}")
        self._temp_dirs.clear()

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

    async def _run_agent_get_final_response(self, agent, input_text: str, expect_json: bool = False) -> str | List[Dict[str, str]] | None:
        """Helper to run an agent with simple text input and get the final response.
        
        Args:
            agent: The agent instance to run.
            input_text: The text input for the agent.
            expect_json: If True, attempts to parse the response as JSON.
            
        Returns:
            The final text response, or a parsed JSON object (list/dict), or None on error.
        """
        # Simplify input based on common patterns for genai models
        # input_content = genai.Content(role='user', parts=[genai.Part(text=input_text)]) # Old way
        final_response_output = None

        logger.debug(f"Running agent '{agent.name}' with input type: {type(input_text)}")
        # Input logging removed for brevity, especially with JSON

        try:
            # Pass input_text directly, assuming run_async handles string input
            # or expects a format the calling code provides (like summaries_json)
            agent_call = agent.run_async(input_text)
            async for event in agent_call:
                logger.debug(f"Event from {agent.name}: {event.model_dump_json(indent=2, exclude_none=True)}")
                if event.is_final_response():
                    if event.content and event.content.parts:
                        raw_text = event.content.parts[0].text
                        if expect_json:
                            try:
                                final_response_output = json.loads(raw_text)
                            except json.JSONDecodeError as json_err:
                                logger.error(f"Agent {agent.name} failed to return valid JSON: {json_err}. Raw text: {raw_text[:500]}")
                                final_response_output = None # Indicate error
                        else:
                            final_response_output = raw_text
                    break # Found final response
                    
            if final_response_output is not None:
                 logger.debug(f"Agent '{agent.name}' finished. Final response type: {type(final_response_output)}")
            else:
                 logger.warning(f"Agent '{agent.name}' did not produce a final response or failed JSON parsing.")
                 
            return final_response_output
            
        except TypeError as te:
            # Catch specific error if run_async returns a coroutine instead of async iterator
            if "__aiter__" in str(te):
                logger.error(f"Error running agent {agent.name}: run_async did not return an async iterator (maybe it returned a coroutine?). {te}")
            else:
                logger.error(f"TypeError during agent {agent.name} execution: {te}")
            return None # Indicate error
        except Exception as e:
            logger.error(f"Error running agent {agent.name}: {e}")
            return None # Indicate error

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

        try:
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

            # --- 2. Summarize Transcripts (Using SummarizerAgent) ---
            logger.info("Step 2: Summarizing transcripts...")
            summaries = []
            if not transcripts:
                logger.warning("No transcripts available to summarize.")
            else:
                try:
                    logger.info(f"Calling SummarizerAgent for {len(transcripts)} transcripts...")
                    # Use asyncio.gather to run summarizer for each transcript concurrently
                    summary_tasks = [
                        self._run_agent_get_final_response(self.summarizer, transcript)
                        for transcript in transcripts.values()
                    ]
                    summaries = await asyncio.gather(*summary_tasks)
                    logger.info(f"Summarization step complete. Generated {len(summaries)} summaries.")
                except Exception as e:
                    logger.exception("Error during transcript summarization step.")
                    summaries = [] # Clear summaries on error

            # --- 3. Synthesize Dialogue (Using SynthesizerAgent) ---
            logger.info("Step 3: Synthesizing dialogue...")
            dialogue_script = []
            if not summaries:
                logger.warning("No summaries available to synthesize dialogue.")
            else:
                try:
                    # Convert summaries list to JSON string for input
                    summaries_json = json.dumps(summaries)
                    logger.info(f"Calling SynthesizerAgent with {len(summaries)} summaries (as JSON)...")
                    
                    # Call the agent using the helper, expecting JSON output
                    dialogue_result = await self._run_agent_get_final_response(
                        self.synthesizer,
                        summaries_json,
                        expect_json=True
                    )

                    # Check if the result is the expected list format
                    if isinstance(dialogue_result, list):
                        dialogue_script = dialogue_result
                        logger.info(f"Synthesized dialogue script with {len(dialogue_script)} lines.")
                        logger.debug(f"Dialogue preview: {json.dumps(dialogue_script[:2], indent=2)}")
                    elif dialogue_result is None:
                        logger.error("SynthesizerAgent failed to produce a valid response or JSON.")
                        dialogue_script = [] # Ensure it's an empty list on error
                    else:
                        logger.error(f"SynthesizerAgent returned unexpected type: {type(dialogue_result)}. Expected list.")
                        dialogue_script = [] # Ensure it's an empty list on error

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

                    logger.info(f"[SIMULATED] Calling AudioGenerator tool (generate_audio_segment) {len(dialogue_script)} times...")
                    # --- Replace below with actual async agent/tool call: ---
                    # This might involve calling audio_generator agent or the tool directly
                    # If using the tool directly:
                    tasks = []
                    for i, segment in enumerate(dialogue_script):
                        speaker = segment.get("speaker", "A") # Default to A if missing
                        line = segment.get("line", "")
                        if not line:
                            logger.warning(f"Skipping empty line in dialogue segment {i}.")
                            continue
                        
                        output_filename = f"segment_{i:03d}_{speaker}.mp3"
                        output_filepath = os.path.join(temp_segment_dir, output_filename)
                        
                        # Call tool function directly
                        # Note: Passing tts_client might improve performance by reusing it
                        task = asyncio.create_task(generate_audio_segment_tool.func(
                            text=line,
                            speaker=speaker,
                            output_filepath=output_filepath,
                            tts_client=tts_client # Pass the client
                        ))
                        tasks.append(task)
                    
                    # Wait for all segment generation tasks
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Collect successful results
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            logger.error(f"Error generating segment {i}: {result}")
                        elif result: # Successful path returned
                            segment_files.append(result)
                            logger.debug(f"Successfully generated audio segment: {result}")
                        else: # Function returned None (likely internal error)
                            logger.error(f"Failed to generate audio segment {i} (tool returned None).")
                            # Decide whether to stop the whole process or continue without this segment
                            # For now, we continue, but the concatenation might fail or be incomplete
                    # -----------------------------------------------------------

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

            # --- Prepare result ---
            # Determine overall status
            if final_audio_path:
                status = "success"
            elif dialogue_script:
                status = "partial_failure_audio"
            elif summaries:
                status = "partial_failure_synthesis"
            elif transcripts:
                status = "partial_failure_summarization"
            elif failed_fetches == video_ids:
                 status = "failure_transcript_fetch"
            else: # Some transcripts fetched, but none summarized? Or other edge cases
                status = "unknown_failure"

            result_dict = {
                "status": status, # Standardized status
                "success": status == "success", # Added boolean success flag
                "dialogue_script": dialogue_script,
                "failed_transcripts": failed_fetches,
                "summary_count": len(summaries),
                "final_audio_path": final_audio_path,
                "error": None # Add error field, populate if needed
            }
            # Add error message for specific failure types if helpful
            if status == "failure_transcript_fetch":
                result_dict["error"] = "Failed to fetch any transcripts."
            elif status == "partial_failure_summarization":
                result_dict["error"] = "Failed during summarization step."
            elif status == "partial_failure_synthesis":
                result_dict["error"] = "Failed during synthesis step."
            elif status == "partial_failure_audio":
                result_dict["error"] = "Failed during audio generation or combination."

            logger.debug(f"Returning result: {json.dumps(result_dict, indent=2)}")
            return result_dict

        except Exception as pipeline_error:
            # Catch unexpected errors during the main pipeline flow
            logger.exception("Unhandled exception during pipeline execution.")
            # Return a standardized error structure
            return {
                "status": "pipeline_error",
                "success": False,
                "dialogue_script": [],
                "failed_transcripts": video_ids, # Assume all failed if pipeline error occurred
                "summary_count": 0,
                "final_audio_path": None,
                "error": f"Pipeline execution error: {pipeline_error}"
            }

        finally:
            # Cleanup temporary directory if it was created
            logger.debug(f"Entering finally block. Temp dir: {temp_segment_dir}") # Log entry into finally
            if temp_segment_dir and os.path.exists(temp_segment_dir):
                logger.info(f"Cleaning up temporary directory: {temp_segment_dir}")
                try:
                    shutil.rmtree(temp_segment_dir)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary directory {temp_segment_dir}: {e}")

        logger.info("Async pipeline finished.")
        # The final return outside try/finally should ideally not be reached 
        # due to returns within try/except, but keep a fallback.
        logger.error("Pipeline execution finished unexpectedly outside try/except block.")
        return {
            "status": "unexpected_exit",
            "success": False, 
            "dialogue_script": [],
            "failed_transcripts": video_ids,
            "summary_count": 0,
            "final_audio_path": None,
            "error": "Pipeline finished unexpectedly."
        }

    # Keep the synchronous wrapper for now, calling the async version
    # This requires the main script to run asyncio.run()
    def run_pipeline(self, video_ids: List[str], output_dir: str = "./output_audio") -> Dict[str, any]:
        logger.warning("Running pipeline synchronously using asyncio.run(). Consider running the main script asynchronously.")
        try:
            # Pass output_dir to the async function
            return asyncio.run(self.run_pipeline_async(video_ids, output_dir=output_dir))
        except RuntimeError as e:
            logger.error(f"RuntimeError running async pipeline (maybe loop already running?): {e}")
            # Fallback or re-raise depending on desired behavior
            return {"status": "error", "error": str(e), "dialogue_script": [], "failed_transcripts": video_ids, "summary_count": 0, "final_audio_path": None} # Ensure all keys present on error
        except Exception as e:
            logger.exception("Unexpected error running async pipeline wrapper.")
            return {"status": "error", "error": str(e), "dialogue_script": [], "failed_transcripts": video_ids, "summary_count": 0, "final_audio_path": None} # Ensure all keys present on error 