"""
Summarizer Agent for processing transcript text and generating summaries.
"""
import logging

# Import BaseAgent
from .base_agent import BaseAgent
# Import any necessary tool types if needed later
# from google.adk.tools import BaseTool

logger = logging.getLogger(__name__)

class SummarizerAgent(BaseAgent):
    """Agent responsible for summarizing transcript text using an LLM."""

    def __init__(self):
        """Initialize the SummarizerAgent."""
        agent_name = "SummarizerAgent"
        # Instruction for the LLM
        agent_instruction = ("""
        You are an expert summarization agent.
        Your task is to read the provided podcast transcript text and generate a concise summary highlighting the key points, topics discussed, and main conclusions.
        Focus on extracting the most important information and presenting it clearly.
        The input will be the full transcript text.
        The output should be the summary text only.
        """)

        # This agent primarily relies on the LLM's instruction-following capability
        # It might not need specific external tools initially.
        agent_tools = [] # No specific tools defined yet

        # Initialize the BaseAgent
        super().__init__(
            name=agent_name,
            instruction=agent_instruction,
            tools=agent_tools
            # We can override the default model here if needed, e.g.:
            # model='gemini-1.5-flash-latest'
        )
        logger.info(f"SummarizerAgent initialized.")

    # The core summarization logic will be handled by the LlmAgent's run method
    # based on the instruction and the input provided to it. We might add
    # specific methods here later if pre/post-processing is needed. 