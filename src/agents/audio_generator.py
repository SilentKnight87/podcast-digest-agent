"""
AudioGenerator Agent responsible for converting a dialogue script into a final audio file.
"""

import logging

# Use absolute paths for imports from src
from src.agents.base_agent import BaseAgent
from src.tools.audio_tools import generate_audio_segment_tool, combine_audio_segments_tool

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

    # Note: The actual orchestration logic (looping through script, calling tools,
    # managing temp files) would typically reside in the agent's run method
    # or potentially be handled by the PipelineRunner calling the tools directly
    # based on the agent's plan or a predefined sequence.
    # For now, the agent definition primarily serves to bundle the tools and instructions. 