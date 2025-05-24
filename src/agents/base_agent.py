"""
Base Agent class for the Podcast Digest project.

This class will contain common functionalities and configurations
for other agents based on the Google Generative AI framework.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import google.generativeai as genai
from google.genai.types import Content, Part
from utils.base_tool import Tool

logger = logging.getLogger(__name__)


DEFAULT_MODEL_ID = "gemini-2.5-flash-preview-04-17"


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
        name: str | None = None,
        instruction: str | None = None,
        tools: list[Tool] | None = None,
        **kwargs,
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

    async def run(self, input_data: Any) -> dict[str, Any]:
        """Run the agent with the given input.

        Constructs a prompt, calls the LLM, and returns the response.

        Args:
            input_data: The input data for the agent to process.

        Returns:
            Dict containing the agent's response text.
        """
        prompt_parts = []
        if self.instruction:
            prompt_parts.append(self.instruction)

        tools_prompt = self._format_tools_for_prompt()
        if tools_prompt:
            # Basic tool description inclusion, no function calling yet
            prompt_parts.append(tools_prompt)

        # Assume input_data is directly usable as prompt content for now
        if isinstance(input_data, str):
            prompt_parts.append(input_data)
        elif isinstance(input_data, list):  # Handle list of strings/parts
            prompt_parts.extend(input_data)
        else:
            # Attempt to convert other types to string, might need refinement
            prompt_parts.append(str(input_data))

        full_prompt_text = "\n\n".join(prompt_parts)
        logger.debug(
            f"Agent {self.name} sending prompt: {full_prompt_text[:500]}..."
        )  # Log truncated prompt

        # Create a Content object from the prompt text
        prompt_content = Content(parts=[Part(text=full_prompt_text)])

        try:
            response = await self.llm.generate_content_async(prompt_content)
            # TODO: Add more robust response handling, error checking, and tool call logic

            # Check if response has 'text' attribute, handle potential blocks/parts later
            response_text = ""
            if hasattr(response, "text"):
                response_text = response.text
            elif hasattr(response, "parts") and response.parts:
                # Simple handling for now, concatenate text from parts
                response_text = "".join(
                    part.text for part in response.parts if hasattr(part, "text")
                )

            logger.info(f"Agent {self.name} received response.")
            return {"response": response_text}
        except Exception as e:
            logger.error(f"Agent {self.name} encountered an error during run: {e}", exc_info=True)
            # TODO: Implement more specific error handling and potentially yield ERROR events
            return {"error": str(e)}

    def _format_tools_for_prompt(self) -> str:
        """Format the tools list into a string for the prompt."""
        if not self.tools:
            return ""

        tools_str = "Available tools:\n"
        for tool in self.tools:
            tools_str += f"- {tool.name}: {tool.description}\n"
        return tools_str
