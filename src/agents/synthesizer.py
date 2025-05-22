"""
Synthesizer Agent for generating dialogue scripts from summaries.
"""
import logging
import json
from typing import AsyncGenerator, List, Dict

# Import BaseAgentEvent types
from .base_agent import BaseAgent, BaseAgentEvent, BaseAgentEventType 
from google.genai.types import Content, Part, GenerateContentResponse
# Import the specific exception
from google.generativeai.types import BlockedPromptException

logger = logging.getLogger(__name__)

DEFAULT_SYNTHESIZER_INSTRUCTION = (
    "You are a scriptwriter tasked with creating a natural-sounding dialogue between two people (Speaker A and Speaker B) that summarizes the key points from a list of provided podcast summaries. "
    "Weave the main ideas from the summaries into a conversational flow. Alternate speakers naturally. "
    "Ensure the dialogue captures the essence of the summaries concisely."
    "IMPORTANT: Format your ENTIRE output ONLY as a valid JSON list of dictionaries, where each dictionary has two keys: 'speaker' (string: 'A' or 'B') and 'line' (string: the spoken text). "
    "Example: [{'speaker': 'A', 'line': '...'}, {'speaker': 'B', 'line': '...'}]"
    "Do not include any introductory text, explanations, or markdown formatting outside the JSON list."
)

class SynthesizerAgent(BaseAgent):
    """Agent responsible for generating a dialogue script from summaries."""

    def __init__(self, **kwargs):
        """Initialize the SynthesizerAgent."""
        super().__init__(
            name="SynthesizerAgent",
            instruction=DEFAULT_SYNTHESIZER_INSTRUCTION,
            **kwargs
        )
        logger.info(f"SynthesizerAgent initialized.")

    async def run_async(self, summaries_json: str) -> AsyncGenerator[BaseAgentEvent, None]:
        """Runs the dialogue synthesis process asynchronously.

        Args:
            summaries_json: A JSON string representing a list of summaries.

        Yields:
            BaseAgentEvent: Events indicating the progress and final result (dialogue script).
        """
        logger.info(f"{self.name}: Received summaries for dialogue synthesis.")
        yield BaseAgentEvent(type=BaseAgentEventType.PROGRESS, payload={'status': 'Starting dialogue synthesis'})

        # --- Parse Input ---
        try:
            summaries: List[str] = json.loads(summaries_json)
            if not isinstance(summaries, list):
                raise ValueError("Input must be a JSON list of strings.")
            logger.info(f"{self.name}: Parsed {len(summaries)} summaries.")
        except json.JSONDecodeError as e:
            logger.error(f"{self.name}: Failed to parse input JSON: {e}")
            yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': f"Invalid input JSON: {e}"})
            return
        except ValueError as e:
            logger.error(f"{self.name}: Invalid input data structure: {e}")
            yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': str(e)})
            return

        if not summaries:
             logger.warning(f"{self.name}: Received empty list of summaries. Nothing to synthesize.")
             yield BaseAgentEvent(type=BaseAgentEventType.RESULT, payload={'dialogue': []}) # Return empty dialogue
             return
             
        # --- Construct Prompt ---
        # Combine summaries into a numbered list for the prompt
        summaries_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(summaries)])
        prompt_text = f"{self.instruction}\n\nPodcast Summaries:\n{summaries_text}\n\nDialogue Script (JSON):"
        
        # Fix: Create the prompt as a simple string, not a Content object
        # The LLM will automatically convert it to appropriate Parts
        prompt_content = prompt_text

        # --- Call LLM and Process Response ---
        try:
            logger.info(f"{self.name}: Sending request to LLM...")
            response: GenerateContentResponse # Declare type hint
            # Add specific try/except around the API call for BlockedPromptException
            try:
                # Pass the Content object directly
                response = await self.llm.generate_content_async(prompt_content)
            except BlockedPromptException as bpe:
                logger.error(f"{self.name}: Prompt blocked by API before generation: {bpe}")
                error_message = f"Error: Prompt blocked by API safety filters. Details: {bpe}"
                yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message})
                return # Stop processing if prompt is blocked
                
            logger.info(f"{self.name}: Received response from LLM.")

            # --- Enhanced Response Processing (similar to SummarizerAgent) ---
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                # Handle blocking
                block_reason = response.prompt_feedback.block_reason.name
                block_message = response.prompt_feedback.block_reason_message
                logger.error(f"{self.name}: Content blocked by API. Reason: {block_reason}. Message: {block_message}")
                error_message = f"Error: Content blocked by API ({block_reason}). {block_message}"
                yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message})
                return

            if not response.candidates:
                # Handle no candidates
                logger.error(f"{self.name}: No candidates found in LLM response: {response}")
                error_message = "Error: No response candidates received from LLM."
                yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message})
                return

            candidate = response.candidates[0]
            
            if candidate.finish_reason != 1: # FINISH_REASON_STOP
                # Handle bad finish reason
                finish_reason_name = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
                logger.error(f"{self.name}: LLM generation stopped for reason: {finish_reason_name}. Message: {candidate.finish_message}")
                safety_info = ""
                if candidate.safety_ratings:
                    safety_info = " Safety Ratings: " + ", ".join([f"{r.category.name}: {r.probability.name}" for r in candidate.safety_ratings])
                error_message = f"Error: LLM generation failed. Reason: {finish_reason_name}. {candidate.finish_message}{safety_info}"
                yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message})
                return

            if not candidate.content or not candidate.content.parts:
                 # Handle missing content/parts
                 logger.error(f"{self.name}: Candidate content or parts missing in LLM response: {candidate}")
                 error_message = "Error: LLM response candidate is missing content/parts."
                 yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message})
                 return

            # --- Extract and Parse Dialogue JSON ---
            raw_dialogue_text = candidate.content.parts[0].text
            try:
                # Clean potential markdown fences (```json ... ```)
                if raw_dialogue_text.startswith("```json\n"):
                    raw_dialogue_text = raw_dialogue_text[len("```json\n"):]
                if raw_dialogue_text.endswith("\n```"):
                    raw_dialogue_text = raw_dialogue_text[:-len("\n```")]
                
                dialogue_script: List[Dict[str, str]] = json.loads(raw_dialogue_text.strip())
                
                # Basic validation of the parsed structure
                if not isinstance(dialogue_script, list):
                    raise ValueError("Parsed JSON is not a list.")
                if dialogue_script and not all(isinstance(item, dict) and 'speaker' in item and 'line' in item for item in dialogue_script):
                     raise ValueError("Parsed JSON list items do not match expected format {'speaker': ..., 'line': ...}.")
                     
                logger.info(f"{self.name}: Dialogue script generated and parsed successfully ({len(dialogue_script)} lines).")
                yield BaseAgentEvent(type=BaseAgentEventType.RESULT, payload={'dialogue': dialogue_script})
                
            except json.JSONDecodeError as e:
                logger.error(f"{self.name}: Failed to parse LLM response as JSON: {e}. Raw text: {raw_dialogue_text[:500]}")
                error_message = f"Error: Failed to parse dialogue script from LLM response - {e}"
                yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message, 'raw_response': raw_dialogue_text})
            except ValueError as e:
                logger.error(f"{self.name}: Parsed JSON structure validation failed: {e}. Raw text: {raw_dialogue_text[:500]}")
                error_message = f"Error: LLM response was not in the expected JSON format - {e}"
                yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message, 'raw_response': raw_dialogue_text})

        except Exception as e:
            logger.error(f"{self.name}: Error during LLM call or response processing: {e}", exc_info=True)
            error_message = f"Error: An exception occurred during dialogue synthesis - {e}"
            yield BaseAgentEvent(type=BaseAgentEventType.ERROR, payload={'error': error_message}) 