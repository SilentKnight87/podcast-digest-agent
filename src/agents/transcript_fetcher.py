"""
TranscriptFetcher Agent for fetching YouTube transcripts using Google ADK.
"""

import logging

# Import the tools using relative path
from ..tools.transcript_tools import fetch_transcript, fetch_transcripts

# Import BaseAgent using relative path
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


# Define the agent class inheriting from BaseAgent
class TranscriptFetcher(BaseAgent):
    """Agent responsible for fetching transcripts from YouTube videos."""

    def __init__(self):
        """Initialize the TranscriptFetcher agent."""
        agent_name = "TranscriptFetcher"
        # Instructions should refer to the tool names
        agent_instruction = """
        You are a helpful agent that fetches transcripts from YouTube videos.
        When given a video ID or URL, you will attempt to fetch its transcript and format it nicely.
        If there are any errors, you will explain them clearly to the user.
        Use the fetch_transcript tool for single videos and fetch_transcripts for multiple videos.
        """

        # Define the list of tools this agent can use
        agent_tools = [fetch_transcript, fetch_transcripts]

        # Initialize the BaseAgent, passing the tools
        super().__init__(name=agent_name, instruction=agent_instruction, tools=agent_tools)
        logger.info(
            f"TranscriptFetcher agent initialized with tools: {[tool.name for tool in agent_tools]}"
        )

    # Tool methods are now removed from the agent class itself
