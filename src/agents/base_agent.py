"""
Base Agent class for the Podcast Digest project.

This class will contain common functionalities and configurations
for other agents based on the Google ADK framework.
"""

import logging
from typing import List, Optional

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools import BaseTool

logger = logging.getLogger(__name__)

# Default model from ADK docs/examples
DEFAULT_MODEL_ID = 'gemini-pro'

class BaseAgent(LlmAgent):
    """Base class for all agents in the Podcast Digest project."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL_ID,
        name: Optional[str] = None,
        instruction: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
        **kwargs
    ):
        """Initialize the BaseAgent.

        Args:
            model: The LLM model ID to use (defaults to gemini-pro).
            name: The name of the agent.
            instruction: Instructions for the agent's behavior.
            tools: A list of tools the agent can use.
            **kwargs: Additional keyword arguments passed to the LlmAgent.
        """
        # Ensure tools is a list for Pydantic validation
        if tools is None:
            tools = []
        
        super().__init__(
            model=model,
            name=name,
            instruction=instruction,
            tools=tools,
            **kwargs
        )
        logger.info(f"Initialized agent: {self.name} with model: {self.model}")

    # Potential common methods can be added here later
    # e.g., common error handling, state management helpers 