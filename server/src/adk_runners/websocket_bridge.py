"""
Bridge between ADK events and WebSocket connections.
"""

import logging

from src.core import task_manager

logger = logging.getLogger(__name__)


class AdkWebSocketBridge:
    """Bridges ADK events to WebSocket updates."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.agent_mapping = {
            "PodcastDigestAgent": "podcast-digest-agent",
            "TranscriptFetcher": "transcript-fetcher",
            "TranscriptFetcherAgent": "transcript-fetcher",
            "SummarizerAgent": "summarizer-agent",
            "DialogueCreatorAgent": "synthesizer-agent",
            "DialogueSynthesizer": "synthesizer-agent",
            "AudioGenerator": "audio-generator",
            "AudioGeneratorAgent": "audio-generator",
            "PodcastDigestSequentialAgent": "podcast-digest-agent",
        }
        self.agent_progress = {}
        self.first_event_seen = False

    async def process_adk_event(self, event) -> None:
        """Process ADK event and send WebSocket updates.

        Args:
            event: ADK Event object
        """
        try:
            # Log the event for debugging
            logger.debug(f"Processing ADK event: {event}")

            # Mark first event
            if not self.first_event_seen:
                self.first_event_seen = True
                logger.info(f"First ADK event for task {self.task_id}")
                task_manager.update_data_flow_status(
                    self.task_id, "youtube-node", "transcript-fetcher", "transferring"
                )

            # ADK events are objects with various attributes
            if hasattr(event, "author") and event.author:
                agent_name = event.author
                agent_id = self.agent_mapping.get(agent_name, "podcast-digest-agent")

                # Initialize progress if needed
                if agent_id not in self.agent_progress:
                    self.agent_progress[agent_id] = 10
                    task_manager.update_agent_status(
                        task_id=self.task_id, agent_id=agent_id, new_status="running", progress=10
                    )

                # Handle tool calls (from event content parts)
                if hasattr(event, "content") and event.content and hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            func_call = part.function_call
                            tool_name = (
                                func_call.name if hasattr(func_call, "name") else str(func_call)
                            )

                            logger.info(f"Tool called: {tool_name} by {agent_name}")
                            task_manager.add_agent_log(
                                self.task_id, agent_id, f"Calling tool: {tool_name}", "info"
                            )

                            # Update progress
                            self.agent_progress[agent_id] = min(
                                self.agent_progress[agent_id] + 20, 80
                            )
                            task_manager.update_agent_status(
                                task_id=self.task_id,
                                agent_id=agent_id,
                                new_status="running",
                                progress=self.agent_progress[agent_id],
                            )

                        elif hasattr(part, "function_response") and part.function_response:
                            # Handle function responses
                            logger.info(f"Tool response received for {agent_name}")
                            self.agent_progress[agent_id] = min(
                                self.agent_progress[agent_id] + 10, 90
                            )
                            task_manager.update_agent_status(
                                task_id=self.task_id,
                                agent_id=agent_id,
                                new_status="running",
                                progress=self.agent_progress[agent_id],
                            )

                # Handle content/messages
                if hasattr(event, "content") and event.content:
                    # Log content if it has text
                    if hasattr(event.content, "parts"):
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                # Log first 200 chars of content
                                log_text = (
                                    part.text[:200] + "..." if len(part.text) > 200 else part.text
                                )
                                task_manager.add_agent_log(self.task_id, agent_id, log_text, "info")

                # Check for completion
                if hasattr(event, "actions") and event.actions:
                    if hasattr(event.actions, "state_delta") and event.actions.state_delta:
                        # Check if we have final outputs in state
                        state_delta = event.actions.state_delta

                        if "final_audio_path" in state_delta:
                            # Audio generation completed
                            task_manager.update_agent_status(
                                task_id=self.task_id,
                                agent_id="audio-generator",
                                new_status="completed",
                                progress=100,
                            )
                            task_manager.update_data_flow_status(
                                self.task_id, "synthesizer-agent", "audio-generator", "completed"
                            )
                            task_manager.update_data_flow_status(
                                self.task_id, "audio-generator", "ui-player", "completed"
                            )
                            # Mark UI player as completed when audio is ready
                            task_manager.update_agent_status(
                                task_id=self.task_id,
                                agent_id="ui-player",
                                new_status="completed",
                                progress=100,
                            )

                        if "dialogue_script" in state_delta:
                            # Dialogue synthesis completed
                            # First, mark summarizer as completed (since dialogue agent does both)
                            task_manager.update_agent_status(
                                task_id=self.task_id,
                                agent_id="summarizer-agent",
                                new_status="completed",
                                progress=100,
                            )
                            task_manager.update_data_flow_status(
                                self.task_id, "transcript-fetcher", "summarizer-agent", "completed"
                            )

                            # Then mark synthesizer as completed
                            task_manager.update_agent_status(
                                task_id=self.task_id,
                                agent_id="synthesizer-agent",
                                new_status="completed",
                                progress=100,
                            )
                            task_manager.update_data_flow_status(
                                self.task_id, "summarizer-agent", "synthesizer-agent", "completed"
                            )

                        if "summaries" in state_delta:
                            # Summarization completed
                            task_manager.update_agent_status(
                                task_id=self.task_id,
                                agent_id="summarizer-agent",
                                new_status="completed",
                                progress=100,
                            )
                            task_manager.update_data_flow_status(
                                self.task_id, "transcript-fetcher", "summarizer-agent", "completed"
                            )

                        if "transcripts" in state_delta:
                            # Transcript fetching completed
                            task_manager.update_agent_status(
                                task_id=self.task_id,
                                agent_id="transcript-fetcher",
                                new_status="completed",
                                progress=100,
                            )
                            task_manager.update_data_flow_status(
                                self.task_id, "youtube-node", "transcript-fetcher", "completed"
                            )

        except Exception as e:
            logger.error(f"Error processing ADK event: {e}", exc_info=True)
            # Don't let errors stop the pipeline
