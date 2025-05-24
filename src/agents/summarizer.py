"""
Summarizer Agent for processing transcript text and generating summaries.
"""

import logging
from collections.abc import AsyncGenerator

from google.genai.types import GenerateContentResponse

from .base_agent import BaseAgent, BaseAgentEvent, BaseAgentEventType

# Import any necessary tool types if needed later
# from google.adk.tools import BaseTool

logger = logging.getLogger(__name__)

DEFAULT_SUMMARIZER_INSTRUCTION = (
    "You are an expert podcast summarizer. Given the transcript of a podcast episode, "
    "provide a concise yet comprehensive summary capturing the key topics, discussions, "
    "and conclusions. Focus on the main points and insights presented."
)


class SummarizerAgent(BaseAgent):
    """Agent responsible for summarizing podcast transcripts."""

    def __init__(self, **kwargs):
        """Initialize the SummarizerAgent."""
        super().__init__(
            name="SummarizerAgent", instruction=DEFAULT_SUMMARIZER_INSTRUCTION, **kwargs
        )
        logger.info("SummarizerAgent initialized.")

    async def run_async(self, transcript: str) -> AsyncGenerator[BaseAgentEvent, None]:
        """Runs the summarization process asynchronously.

        Args:
            transcript: The podcast transcript text to summarize.

        Yields:
            BaseAgentEvent: Events indicating the progress and final result.
        """
        logger.info(
            f"{self.name}: Received transcript for summarization (length: {len(transcript)})."
        )
        yield BaseAgentEvent(
            type=BaseAgentEventType.PROGRESS, payload={"status": "Starting summarization"}
        )

        # --- Construct Prompt ---
        prompt_text = f"{self.instruction}\n\nTranscript:\n{transcript}\n\nSummary:"
        # Fix: Create the prompt as a simple string, not a Content object
        # The LLM will automatically convert it to appropriate Parts
        prompt_content = prompt_text

        # --- Call LLM and Process Response ---
        try:
            logger.info(f"{self.name}: Sending request to LLM...")
            response: GenerateContentResponse
            # Add specific try/except around the API call for BlockedPromptException
            try:
                # Pass the string directly to generate_content_async
                response = await self.llm.generate_content_async(prompt_content)
            except Exception as bpe:
                # Using generic exception as BlockedPromptException might not be defined
                logger.error(f"{self.name}: Prompt blocked by API before generation: {bpe}")
                error_message = f"Error: Prompt blocked by API ({bpe})."
                yield BaseAgentEvent(
                    type=BaseAgentEventType.ERROR, payload={"error": error_message}
                )
                return  # Stop processing if the prompt itself is blocked

            logger.info(f"{self.name}: Received response from LLM.")

            # --- Enhanced Response Processing ---

            # 1. Check for Prompt Feedback/Blocking
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason.name
                block_message = response.prompt_feedback.block_reason_message
                logger.error(
                    f"{self.name}: Content blocked by API. Reason: {block_reason}. Message: {block_message}"
                )
                error_message = f"Error: Content blocked by API ({block_reason}). {block_message}"
                yield BaseAgentEvent(
                    type=BaseAgentEventType.ERROR, payload={"error": error_message}
                )
                return  # Stop processing if blocked

            # 2. Check Candidates List
            if not response.candidates:
                logger.error(f"{self.name}: No candidates found in LLM response: {response}")
                error_message = "Error: No response candidates received from LLM."
                yield BaseAgentEvent(
                    type=BaseAgentEventType.ERROR, payload={"error": error_message}
                )
                return

            # 3. Process the first candidate (usually only one for non-streaming)
            candidate = response.candidates[0]

            # 4. Check Finish Reason
            # See FinishReason enum in google.generativeai.types
            # We expect STOP for a successful completion.
            if candidate.finish_reason != 1:  # FINISH_REASON_STOP = 1
                finish_reason_name = (
                    candidate.finish_reason.name
                    if hasattr(candidate.finish_reason, "name")
                    else str(candidate.finish_reason)
                )
                logger.error(
                    f"{self.name}: LLM generation stopped for reason: {finish_reason_name}. Message: {candidate.finish_message}"
                )
                # Add safety ratings info if available
                safety_info = ""
                if candidate.safety_ratings:
                    safety_info = " Safety Ratings: " + ", ".join(
                        [
                            f"{r.category.name}: {r.probability.name}"
                            for r in candidate.safety_ratings
                        ]
                    )
                error_message = f"Error: LLM generation failed. Reason: {finish_reason_name}. {candidate.finish_message}{safety_info}"
                yield BaseAgentEvent(
                    type=BaseAgentEventType.ERROR, payload={"error": error_message}
                )
                return

            # 5. Check Content and Parts
            if not candidate.content or not candidate.content.parts:
                logger.error(
                    f"{self.name}: Candidate content or parts missing in LLM response: {candidate}"
                )
                error_message = "Error: LLM response candidate is missing content/parts."
                yield BaseAgentEvent(
                    type=BaseAgentEventType.ERROR, payload={"error": error_message}
                )
                return

            # 6. Extract Summary Text
            # Assuming the summary is in the first text part
            summary_text = candidate.content.parts[0].text
            logger.info(
                f"{self.name}: Summary generated successfully (length: {len(summary_text)})."
            )
            yield BaseAgentEvent(type=BaseAgentEventType.RESULT, payload={"summary": summary_text})

        except Exception as e:
            # Catch potential API errors or other exceptions during the call/processing
            logger.error(
                f"{self.name}: Error during LLM call or response processing: {e}", exc_info=True
            )
            error_message = f"Error: An exception occurred during summarization - {e}"
            yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={"error": error_message})

    # The core summarization logic will be handled by the LlmAgent's run method
    # based on the instruction and the input provided to it. We might add
    # specific methods here later if pre/post-processing is needed.
