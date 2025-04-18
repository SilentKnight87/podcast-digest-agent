"""
Base Agent class for the Podcast Digest project.

This class will contain common functionalities and configurations
for other agents based on the Google Generative AI framework.
"""

import logging
from typing import List, Optional, Any, Dict
from enum import Enum
from dataclasses import dataclass
import google.generativeai as genai
from pydantic import BaseModel

from utils.base_tool import Tool

logger = logging.getLogger(__name__)

# Default model from Gemini docs
DEFAULT_MODEL_ID = 'gemini-2.5-flash-preview-04-17'

class BaseAgentEventType(Enum):
    """Enum for different types of events an agent might yield."""
    PROGRESS = "progress"
    RESULT = "result"
    ERROR = "error"

@dataclass
class BaseAgentEvent:
    """Dataclass representing an event yielded by an agent."""
    type: BaseAgentEventType
    payload: dict

class BaseAgent:
    """Base class for all agents in the Podcast Digest project."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL_ID,
        name: Optional[str] = None,
        instruction: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        **kwargs
    ):
        """Initialize the BaseAgent.

        Args:
            model: The LLM model ID to use (defaults to gemini-pro).
            name: The name of the agent.
            instruction: Instructions for the agent's behavior.
            tools: A list of tools the agent can use.
            **kwargs: Additional keyword arguments.
        """
        self.model = model
        self.name = name or self.__class__.__name__
        self.instruction = instruction
        self.tools = tools or []
        
        # Initialize the model
        self.llm = genai.GenerativeModel(model)
        logger.info(f"Initialized agent: {self.name} with model: {self.model}")

    async def run(self, input_data: Any) -> Dict[str, Any]:
        """Run the agent with the given input.
        
        Args:
            input_data: The input data for the agent to process.
            
        Returns:
            Dict containing the agent's response and any relevant metadata.
        """
        raise NotImplementedError("Agent must implement run method")

    def _format_tools_for_prompt(self) -> str:
        """Format the tools list into a string for the prompt."""
        if not self.tools:
            return ""
        
        tools_str = "Available tools:\n"
        for tool in self.tools:
            tools_str += f"- {tool.name}: {tool.description}\n"
        return tools_str 