"""
Synthesizer Agent for creating a dialogue script from multiple summaries.
"""
import logging
import json
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SynthesizerAgent(BaseAgent):
    """Agent responsible for synthesizing a dialogue script from summaries."""

    def __init__(self):
        """Initialize the SynthesizerAgent."""
        agent_name = "SynthesizerAgent"
        # Instruction for the LLM - crucial for getting the right format
        agent_instruction = ("""
        You are a scriptwriting agent specializing in creating engaging dialogues.
        Your task is to take a list of podcast summaries and synthesize them into a single, cohesive dialogue script between two speakers: "Speaker A" and "Speaker B".
        Alternate the speakers naturally, weaving the key points from the summaries into a conversation.
        The input will be a JSON string representing a list of summary texts.
        The output MUST be a JSON string representing a list of dictionaries, where each dictionary has "speaker" (either "A" or "B") and "line" (the dialogue text) keys.
        Example Input: ["Summary 1 text...", "Summary 2 text..."]
        Example Output: [{"speaker": "A", "line": "Dialogue line 1..."}, {"speaker": "B", "line": "Dialogue line 2..."}]
        Ensure the output is valid JSON.
        """)

        # This agent also primarily relies on the LLM's instruction-following capability
        agent_tools = [] # No specific tools defined yet

        # Initialize the BaseAgent
        super().__init__(
            name=agent_name,
            instruction=agent_instruction,
            tools=agent_tools
        )
        logger.info(f"SynthesizerAgent initialized.")

    # The core synthesis logic is handled by the LlmAgent based on instruction.
    # We might add methods here for pre-processing input summaries or
    # post-processing/validating the LLM's output JSON. 