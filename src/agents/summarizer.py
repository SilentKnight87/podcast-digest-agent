"""
Summarizer Agent for processing transcript text and generating summaries.
"""
import logging
from typing import AsyncGenerator
from .base_agent import BaseAgent, BaseAgentEvent, BaseAgentEventType
from google.genai.types import Content, Part, GenerateContentResponse
# Import any necessary tool types if needed later
# from google.adk.tools import BaseTool

logger = logging.getLogger(__name__)

DEFAULT_SUMMARIZER_INSTRUCTION = (\
    "You are an expert podcast summarizer. Given the transcript of a podcast episode, "
    "provide a concise yet comprehensive summary capturing the key topics, discussions, "
    "and conclusions. Focus on the main points and insights presented."
)

class SummarizerAgent(BaseAgent):
    """Agent responsible for summarizing podcast transcripts."""

    def __init__(self, **kwargs):
        """Initialize the SummarizerAgent."""
        super().__init__(
            name="SummarizerAgent",
            instruction=DEFAULT_SUMMARIZER_INSTRUCTION,
            **kwargs
        )
        logger.info(f"SummarizerAgent initialized.")

    async def run_async(self, transcript: str) -> AsyncGenerator[BaseAgentEvent, None]:
        """Runs the summarization process asynchronously.

        Args:
            transcript: The podcast transcript text to summarize.

        Yields:
            BaseAgentEvent: Events indicating the progress and final result.
        """
        logger.info(f"{self.name}: Received transcript for summarization (length: {len(transcript)}).")
        yield BaseAgentEvent(type=BaseAgentEventType.PROGRESS, payload={'status': 'Starting summarization'})

        # --- Simple Prompt Construction (can be refined) ---
        prompt = f"{self.instruction}\n\nTranscript:\n{transcript}\n\nSummary:"
        # Create Content object for the prompt
        prompt_content = Content(parts=[Part(text=prompt)])

        try:
            # --- Call LLM (Non-streaming for basic test) ---
            # The test mocks generate_content_async directly on the llm object
            # response: GenerateContentResponse = await self.llm.generate_content_async(prompt)
            response: GenerateContentResponse = await self.llm.generate_content_async(prompt_content)

            # --- Process Response ---
            # Basic response handling based on mock structure in test
            # Actual API response might need more robust checks (e.g., safety ratings)
            if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                summary_text = response.candidates[0].content.parts[0].text
                logger.info(f"{self.name}: Summary generated successfully (length: {len(summary_text)}).")
                # Yield RESULT event
                yield BaseAgentEvent(type=BaseAgentEventType.RESULT, payload={'summary': summary_text})
            else:
                 # Handle cases where response is empty or doesn't have expected structure
                 logger.warning(f"{self.name}: LLM response was empty or invalid: {response}")
                 error_message = "Error: Could not generate summary from LLM response."
                 yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message})

        except Exception as e:
            logger.error(f"{self.name}: Error during LLM call: {e}", exc_info=True)
            error_message = f"Error: An exception occurred during summarization - {e}"
            yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message})

    # The core summarization logic will be handled by the LlmAgent's run method
    # based on the instruction and the input provided to it. We might add
    # specific methods here later if pre/post-processing is needed. 