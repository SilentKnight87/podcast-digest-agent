"""
AudioGenerator Agent responsible for converting a dialogue script into a final audio file.
"""

import logging
import json # Added for parsing input
import os # Added for path manipulation
from typing import Dict, Any

# Use relative paths for imports
from .base_agent import BaseAgent
from ..tools.audio_tools import generate_audio_segment_tool, combine_audio_segments_tool

logger = logging.getLogger(__name__)

class AudioGenerator(BaseAgent):
    """Agent that takes a dialogue script and generates a concatenated audio file."""

    def __init__(self):
        """Initialize the AudioGenerator agent."""
        agent_name = "AudioGenerator"
        # Instruction for the LLM (might not be strictly needed if logic is hardcoded,
        # but good practice for potential future flexibility)
        agent_instruction = ("""
        You are an audio processing agent.
        Your task is to take a structured dialogue script (list of speaker/line dictionaries)
        and an output directory path.
        You will use the available tools to:
        1. Generate an individual audio segment for each line in the script, saving them to a temporary location.
        2. Concatenate all generated segments in the correct order into a single final audio file in the specified output directory.
        3. Report the path to the final audio file upon successful completion.
        The input will likely be a JSON string representing the script and the output directory.
        You must call 'generate_audio_segment' for each line and then 'combine_audio_segments' once with the list of generated file paths.
        """)

        # Define the list of tools this agent can use
        agent_tools = [generate_audio_segment_tool, combine_audio_segments_tool]

        # Initialize the BaseAgent, passing the tools
        super().__init__(
            name=agent_name,
            instruction=agent_instruction,
            tools=agent_tools
        )
        logger.info(f"AudioGenerator agent initialized with tools: {[tool.name for tool in agent_tools]}")

    async def run(self, input_data_str: str) -> Dict[str, Any]:
        """Orchestrates the audio generation process.

        Parses the input script, generates audio for each segment using
        `generate_audio_segment_tool`, combines them using
        `combine_audio_segments_tool`, and returns the path to the final audio file.
        """
        try:
            logger.debug(f"AudioGenerator received input: {input_data_str}")
            input_data = json.loads(input_data_str)
            script = input_data.get("script")
            output_dir = input_data.get("output_dir")

            if not isinstance(script, list) or output_dir is None:
                logger.error(f"Invalid input for AudioGenerator: script (list) and output_dir (string) are required. Got script type: {type(script)}, output_dir: {output_dir}")
                return {"error": "Invalid input: 'script' (list) and 'output_dir' (string) are required."}
            
            if not script: # Handle empty script case
                logger.info("AudioGenerator received an empty script.")
                return {"response": "Cannot generate audio from an empty script."}

            segment_paths = []
            
            gen_tool = next((t for t in self.tools if t.name == "generate_audio_segment"), None)
            if not gen_tool:
                logger.error("generate_audio_segment not found in agent's tools.")
                return {"error": "Configuration error: generate_audio_segment not found."}

            # Ensure output_dir exists (important for tools that write files)
            # The settings module now handles creation of base OUTPUT_AUDIO_DIR, 
            # but specific subdirectories per job might be needed here.
            # For simplicity, we'll assume output_dir is a valid, existing path for now,
            # or that tools handle its creation if they need subdirectories.

            for i, item in enumerate(script):
                text = item.get("text")
                speaker = item.get("speaker") # Voice selection based on speaker can be a future enhancement
                
                if text is None or speaker is None:
                    logger.warning(f"Skipping script item due to missing text or speaker: {item}")
                    continue

                # Define a temporary/intermediate path for the segment. 
                # The actual tool call (mocked in test) will determine the returned path.
                # This path is more of a suggestion if the tool needed it.
                suggested_segment_filename = f"temp_segment_{speaker}_{i}.mp3"
                segment_output_filepath = os.path.join(output_dir, "segments", suggested_segment_filename)
                # Ensure the 'segments' subdirectory exists
                os.makedirs(os.path.dirname(segment_output_filepath), exist_ok=True)

                logger.debug(f"Calling generate_audio_segment_tool for: '{text}'")
                segment_path = await gen_tool.run(
                    text=text,
                    speaker=speaker, # The tool might use this to select a voice
                    output_filepath=segment_output_filepath 
                    # tts_client: If required by the tool, it should be configured within the tool 
                    # or passed via a shared mechanism, not directly here unless run signature demands.
                )
                
                if not segment_path:
                    logger.error(f"Failed to generate segment for: '{text}'. Tool returned None.")
                    return {"error": f"Failed to generate audio segment for: \"{text}\"."}
                segment_paths.append(segment_path)
                logger.info(f"Generated segment: {segment_path}")
            
            if not segment_paths:
                 logger.info("No segments were generated, possibly due to an empty or invalid script content.")
                 return {"response": "No audio segments were generated."}

            combine_tool = next((t for t in self.tools if t.name == "combine_audio_segments"), None)
            if not combine_tool:
                logger.error("combine_audio_segments not found in agent's tools.")
                return {"error": "Configuration error: combine_audio_segments not found."}

            logger.debug(f"Calling combine_audio_segments_tool with segments: {segment_paths}")
            final_output_path = await combine_tool.run(
                segment_filepaths=segment_paths,
                output_dir=output_dir
            )

            if not final_output_path:
                logger.error("Failed to combine audio segments. Tool returned None.")
                return {"error": "Failed to combine audio segments."}
            
            logger.info(f"Successfully generated final audio: {final_output_path}")
            return {"response": f"Successfully generated the final audio file at: {final_output_path}"}

        except json.JSONDecodeError as e:
            logger.error(f"AudioGenerator failed to decode input JSON: {input_data_str}. Error: {e}")
            return {"error": "Invalid JSON input."}
        except Exception as e:
            logger.error(f"AudioGenerator encountered an unexpected error: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred: {str(e)}"}

    # Note: The actual orchestration logic (looping through script, calling tools,
    # managing temp files) would typically reside in the agent's run method
    # or potentially be handled by the PipelineRunner calling the tools directly
    # based on the agent's plan or a predefined sequence.
    # For now, the agent definition primarily serves to bundle the tools and instructions. 