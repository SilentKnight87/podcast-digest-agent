# Google ADK Migration PRD

## Critical Update Notice

⚠️ **IMPORTANT**: This PRD has been completely rewritten based on actual Google ADK v1.0.0 documentation and real-world implementation patterns. The previous version contained significant inaccuracies about ADK APIs and architecture.

## Overview

This specification outlines the migration of the podcast digest backend from custom agent implementation to Google Agent Development Kit (ADK) v1.0.0. ADK was officially released at Google Cloud NEXT 2025 and is now production-ready.

## Research Summary

### Key Findings from ADK Research

1. **ADK is Production Ready** (v1.0.0 as of April 2025)
2. **Fundamentally Different Architecture** than our current implementation
3. **Simplified Agent Model** - no complex session management needed
4. **Different Tool System** - decorator-based vs class-based
5. **Built-in Deployment Support** for Cloud Run and Vertex AI Agent Engine

### Major Compatibility Issues Identified

Our current implementation is **NOT directly compatible** with ADK:

- **Custom BaseAgent** vs ADK `Agent` class
- **Custom Tool classes** vs ADK function decorators
- **Manual pipeline orchestration** vs ADK sub-agent delegation
- **Direct Google AI calls** vs ADK managed execution
- **Custom session management** vs ADK internal handling

## Migration Strategy: Incremental ADK Wrapper Approach

Instead of discarding the proven SimplePipeline, we will **wrap the existing processing logic inside a single ADK `Agent`** and retrofit each helper function as an ADK `@tool`. This preserves all current behaviour while bringing us onto the ADK execution/runtime stack. Multi-agent orchestration can be introduced later if warranted, but is explicitly **out of scope for this first adoption pass**.

## Updated Goals

1. **Incremental adoption** of ADK v1.0.0 by wrapping the current pipeline
2. **Leverage ADK built-in services** (sessions, artifacts, monitoring) with minimal code churn
3. **Guarantee feature parity**—UI contracts, API schemas, and tests remain unchanged
4. **Align code with official ADK patterns** (`@tool`, single-agent quick-start) to ease future refactors
5. **Enable production deployment** (Cloud Run / Agent Engine) once wrapper is stable
6. **Maintain real-time WebSocket updates** for ProcessingVisualizer component

## Key Addition: WebSocket Integration

The migration now includes a dedicated **WebSocket Bridge** (Phase 4) that ensures the frontend ProcessingVisualizer continues to receive real-time updates during ADK processing:

- **AdkWebSocketBridge** class translates ADK events into existing WebSocket message format
- Maintains compatibility with current TaskManager and ConnectionManager
- Preserves all frontend visualization features (agent status, progress bars, data flows)
- No changes required to the frontend ProcessingVisualizer component

## Implementation Plan

### Phase 1: Environment Setup and Verification (1 day)

#### 1.1 Install and Verify ADK

```bash
# Navigate to project root
cd /Users/peterbrown/Documents/Code/podcast-digest-agent

# Activate virtual environment
source venv/bin/activate

# Install ADK v1.0.0 (stable release)
pip install google-adk

# Verify installation with simple test
python -c "
from google.adk.agents import Agent
from google.adk.tools import google_search
print('✅ Google ADK v1.0.0 installed successfully')
print('✅ Core imports working')
"
```

#### 1.2 Study Real ADK Patterns

Create test file to understand actual ADK patterns:

**File**: `adk_research/test_basic_agent.py`

```python
"""
Test basic ADK agent to understand real patterns.
"""
from google.adk.agents import Agent
from google.adk.tools import google_search

# Test basic agent creation (from real documentation)
test_agent = Agent(
    name="test_agent",
    model="gemini-2.5-flash-preview-04-17",
    instruction="You are a helpful assistant.",
    description="Test agent to verify ADK patterns",
    tools=[google_search]  # Built-in tool
)

print(f"✅ Created agent: {test_agent.name}")
print(f"✅ Model: {test_agent.model}")
print(f"✅ Tools: {len(test_agent.tools)}")
```

#### 1.3 Test ADK Web Interface

```bash
# Test ADK web interface
adk web
```

### Phase 2: Minimal ADK Wrapper (1 day)

#### 2.1 Understanding Tool Conversion

**Current Pattern**:
```python
class FetchTranscriptTool(Tool):
    name: str = "fetch_transcript"
    description: str = "Fetches YouTube transcript"

    def run(self, video_id: str) -> dict:
        # Implementation
        return result
```

**ADK Pattern** (based on research):
```python
# ADK uses plain functions, not decorators
def fetch_youtube_transcript(video_id: str) -> dict:
    """Fetches the transcript for a YouTube video.

    Args:
        video_id: The YouTube video ID

    Returns:
        Dictionary containing transcript data
    """
    # Implementation using existing logic
    return result
```

#### 2.2 Create ADK Tools Module

**New file**: `src/adk_tools/transcript_tools.py`

```python
"""
ADK-compatible transcript tools.
"""
import logging
from typing import Dict, Any

from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi
)

logger = logging.getLogger(__name__)

def fetch_youtube_transcript(video_id: str) -> Dict[str, Any]:
    """Fetches the transcript for a single YouTube video.

    Args:
        video_id: The YouTube video ID to fetch transcript for

    Returns:
        Dictionary containing transcript data or error information
    """
    try:
        logger.info(f"Fetching transcript for video: {video_id}")
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=['en', 'en-US', 'en-GB']
        )

        # Combine transcript segments
        full_transcript = " ".join([entry['text'] for entry in transcript_list])

        logger.info(f"Successfully fetched transcript for {video_id} (length: {len(full_transcript)})")
        return {
            "success": True,
            "video_id": video_id,
            "transcript": full_transcript,
            "segment_count": len(transcript_list)
        }

    except (NoTranscriptFound, TranscriptsDisabled) as e:
        logger.warning(f"No transcript available for {video_id}: {e}")
        return {
            "success": False,
            "video_id": video_id,
            "error": f"No transcript available: {e}",
            "transcript": None
        }

    except Exception as e:
        logger.error(f"Error fetching transcript for {video_id}: {e}")
        return {
            "success": False,
            "video_id": video_id,
            "error": f"Fetch error: {e}",
            "transcript": None
        }

def process_multiple_transcripts(video_ids: list[str]) -> Dict[str, Any]:
    """Process multiple video transcripts.

    Args:
        video_ids: List of YouTube video IDs

    Returns:
        Dictionary containing all transcript results
    """
    results = {}
    successful_count = 0

    for video_id in video_ids:
        result = fetch_youtube_transcript(video_id)
        results[video_id] = result
        if result["success"]:
            successful_count += 1

    return {
        "results": results,
        "total_videos": len(video_ids),
        "successful_count": successful_count,
        "failed_count": len(video_ids) - successful_count
    }
```

**New file**: `src/adk_tools/audio_tools.py`

```python
"""
ADK-compatible audio generation tools.
"""
import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pydub
from google.cloud import texttospeech_v1

logger = logging.getLogger(__name__)

# Voice configurations (from existing implementation)
DEFAULT_VOICE_CONFIG = {
    "A": {
        "language_code": "en-US",
        "name": "en-US-Journey-D",
        "ssml_gender": texttospeech_v1.SsmlVoiceGender.MALE,
    },
    "B": {
        "language_code": "en-US",
        "name": "en-US-Journey-F",
        "ssml_gender": texttospeech_v1.SsmlVoiceGender.FEMALE,
    }
}

async def generate_audio_from_dialogue(dialogue_script: str, output_dir: str) -> Dict[str, Any]:
    """Generate audio from dialogue script using Google Cloud TTS.

    Args:
        dialogue_script: JSON string containing dialogue with speaker/line format
        output_dir: Directory to save the final audio file

    Returns:
        Dictionary containing audio generation results
    """
    try:
        # Parse dialogue script
        dialogue = json.loads(dialogue_script)
        if not isinstance(dialogue, list):
            raise ValueError("Dialogue script must be a JSON array")

        # Create temporary directory for segments
        temp_dir = tempfile.mkdtemp(prefix="adk_audio_segments_")
        segment_files = []

        # Initialize TTS client
        async with texttospeech_v1.TextToSpeechAsyncClient() as tts_client:
            # Generate audio segments
            for i, segment in enumerate(dialogue):
                speaker = segment.get("speaker", "A")
                line = segment.get("line", "")

                if not line.strip():
                    continue

                # Generate audio for this segment
                segment_file = await _generate_segment(
                    tts_client, line, speaker, temp_dir, i
                )
                if segment_file:
                    segment_files.append(segment_file)

        # Combine segments
        if segment_files:
            final_audio_path = await _combine_segments(segment_files, output_dir)

            # Cleanup temporary files
            import shutil
            shutil.rmtree(temp_dir)

            return {
                "success": True,
                "audio_path": final_audio_path,
                "segment_count": len(segment_files),
                "error": None
            }
        else:
            return {
                "success": False,
                "audio_path": None,
                "segment_count": 0,
                "error": "No audio segments generated"
            }

    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        return {
            "success": False,
            "audio_path": None,
            "segment_count": 0,
            "error": str(e)
        }

async def _generate_segment(tts_client, text: str, speaker: str, temp_dir: str, index: int) -> str:
    """Generate a single audio segment."""
    try:
        voice_config = DEFAULT_VOICE_CONFIG.get(speaker, DEFAULT_VOICE_CONFIG["A"])

        synthesis_input = texttospeech_v1.SynthesisInput(text=text)
        voice = texttospeech_v1.VoiceSelectionParams(
            language_code=voice_config["language_code"],
            name=voice_config["name"],
            ssml_gender=voice_config["ssml_gender"]
        )
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.MP3
        )

        response = await tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Save segment file
        segment_path = Path(temp_dir) / f"segment_{index:03d}_{speaker}.mp3"
        with open(segment_path, "wb") as f:
            f.write(response.audio_content)

        return str(segment_path)

    except Exception as e:
        logger.error(f"Error generating segment {index}: {e}")
        return None

async def _combine_segments(segment_files: List[str], output_dir: str) -> str:
    """Combine audio segments into final file."""
    try:
        # Load and combine segments
        combined = pydub.AudioSegment.empty()
        for segment_file in sorted(segment_files):
            segment = pydub.AudioSegment.from_mp3(segment_file)
            combined += segment

        # Generate output filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(output_dir) / f"podcast_digest_{timestamp}.mp3"

        # Export final audio
        combined.export(output_file, format="mp3")

        logger.info(f"Combined audio saved to: {output_file}")
        return str(output_file)

    except Exception as e:
        logger.error(f"Error combining segments: {e}")
        raise

### Phase 3: Create ADK Agents (2 days)

#### 3.1 Create Main ADK Agent

**New file**: `src/adk_agents/podcast_agent.py`

```python
"""
Main ADK agent for podcast digest generation.
"""
import logging
from google.adk.agents import Agent, LlmAgent

# Import our ADK-compatible tools
from ..adk_tools.transcript_tools import (
    fetch_youtube_transcript,
    process_multiple_transcripts
)
from ..adk_tools.audio_tools import generate_audio_from_dialogue

logger = logging.getLogger(__name__)

# Specialized sub-agents
transcript_agent = LlmAgent(
    name="TranscriptFetcher",
    model="gemini-2.5-flash-preview-04-17",
    description="Fetches and processes YouTube video transcripts",
    instruction="""
    You are a specialist in fetching YouTube video transcripts.

    Your job is to:
    1. Take YouTube video IDs from the user
    2. Use the fetch_youtube_transcript tool to get transcripts
    3. Report success/failure for each video
    4. Provide the transcript text for successful fetches

    Always be thorough and report any issues clearly.
    """,
    tools=[fetch_youtube_transcript, process_multiple_transcripts]
)

summarizer_agent = LlmAgent(
    name="SummarizerAgent",
    model="gemini-2.5-flash-preview-04-17",
    description="Summarizes podcast transcripts into key insights",
    instruction="""
    You are an expert podcast summarizer.

    Your role is to:
    1. Read transcript text provided by the TranscriptFetcher
    2. Generate concise yet comprehensive summaries
    3. Focus on key topics, main discussions, and important conclusions
    4. Preserve the most valuable insights and information
    5. Aim for summaries that are 10-15% of the original transcript length

    Create summaries that capture the essence while being engaging and informative.
    """,
    output_key="summaries"  # ADK will save outputs to session state
)

synthesizer_agent = LlmAgent(
    name="DialogueSynthesizer",
    model="gemini-2.5-flash-preview-04-17",
    description="Converts summaries into natural conversational dialogue",
    instruction="""
    You are a dialogue synthesizer specializing in creating natural conversations.

    Your task is to:
    1. Read summaries from the SummarizerAgent
    2. Create engaging conversational dialogue between two speakers (A and B)
    3. Make the dialogue feel like a real conversation between knowledgeable hosts
    4. Ensure smooth transitions and natural flow
    5. Format output as JSON with 'speaker' and 'line' keys

    Example format:
    [
        {"speaker": "A", "line": "Welcome to today's podcast digest!"},
        {"speaker": "B", "line": "Today we're covering some fascinating insights..."},
        {"speaker": "A", "line": "That's right, let's dive into the key points..."}
    ]

    Make the conversation engaging, informative, and natural-sounding.
    """,
    output_key="dialogue_script"
)

audio_agent = LlmAgent(
    name="AudioGenerator",
    model="gemini-2.5-flash-preview-04-17",
    description="Generates final audio files from dialogue scripts",
    instruction="""
    You are an audio generator responsible for creating high-quality podcast audio.

    Your responsibilities are to:
    1. Read the dialogue script from the DialogueSynthesizer
    2. Use the generate_audio_from_dialogue tool to create audio
    3. Ensure proper speaker differentiation
    4. Handle any errors gracefully and provide clear status updates
    5. Save the final audio file path for the user

    Ensure high-quality audio generation with clear, natural-sounding speech.
    """,
    tools=[generate_audio_from_dialogue],
    output_key="final_audio_path"
)

# Main coordinating agent using ADK sub-agent pattern
podcast_digest_agent = LlmAgent(
    name="PodcastDigestCoordinator",
    model="gemini-2.5-flash-preview-04-17",
    description="Coordinates the complete podcast digest generation pipeline",
    instruction="""
    You are the main coordinator for podcast digest generation.

    Your workflow is:
    1. Delegate to TranscriptFetcher to get video transcripts
    2. Pass transcripts to SummarizerAgent for summarization
    3. Send summaries to DialogueSynthesizer for conversation creation
    4. Have AudioGenerator create the final audio file
    5. Report the final results to the user

    Coordinate the entire process and provide clear status updates at each step.
    """,
    sub_agents=[
        transcript_agent,
        summarizer_agent,
        synthesizer_agent,
        audio_agent
    ]
)

# Export the main agent
root_agent = podcast_digest_agent
```

#### 3.2 Create Agent Module Structure

**New file**: `src/adk_agents/__init__.py`

```python
"""
ADK agents for podcast digest generation.
"""
from .podcast_agent import root_agent

__all__ = ['root_agent']
```

### Phase 4: WebSocket Integration for Real-time Updates (1 day)

#### 4.1 ADK Session Event Streaming

The current system uses WebSocket connections to send real-time updates to the frontend. Since ADK abstracts away direct agent execution control, we need to implement a bridge between ADK's event system and our WebSocket infrastructure.

**New file**: `src/adk_runners/websocket_bridge.py`

```python
"""
Bridge between ADK events and WebSocket connections.
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from src.core import task_manager
from src.core.connection_manager import manager as ws_manager

logger = logging.getLogger(__name__)

class AdkWebSocketBridge:
    """Bridges ADK events to WebSocket updates."""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.agent_mapping = {
            "TranscriptFetcher": "transcript-fetcher",
            "SummarizerAgent": "summarizer-agent",
            "DialogueSynthesizer": "synthesizer-agent",
            "AudioGenerator": "audio-generator"
        }
        self.current_agent = None
        self.agent_progress = {
            "transcript-fetcher": 0,
            "summarizer-agent": 0,
            "synthesizer-agent": 0,
            "audio-generator": 0
        }

    async def process_adk_event(self, event: Dict[str, Any]) -> None:
        """Process ADK event and send WebSocket updates."""
        event_type = event.get("type", "")

        if event_type == "agent_started":
            await self._handle_agent_started(event)
        elif event_type == "agent_completed":
            await self._handle_agent_completed(event)
        elif event_type == "agent_error":
            await self._handle_agent_error(event)
        elif event_type == "log":
            await self._handle_log_event(event)
        elif event_type == "tool_called":
            await self._handle_tool_event(event)
        elif event_type == "message":
            await self._handle_message_event(event)

    async def _handle_agent_started(self, event: Dict[str, Any]) -> None:
        """Handle agent started event."""
        agent_name = event.get("agent_name", "")
        agent_id = self.agent_mapping.get(agent_name, agent_name.lower())

        self.current_agent = agent_id

        # Update agent status to running
        task_manager.update_agent_status(
            task_id=self.task_id,
            agent_id=agent_id,
            new_status="running",
            progress=10.0
        )

        # Update data flow
        self._update_data_flows(agent_id)

        # Add timeline event
        task_manager.add_timeline_event(
            task_id=self.task_id,
            event_type="agent_started",
            message=f"{agent_name} started processing",
            agent_id=agent_id
        )

        logger.info(f"Agent {agent_name} started for task {self.task_id}")

    async def _handle_agent_completed(self, event: Dict[str, Any]) -> None:
        """Handle agent completed event."""
        agent_name = event.get("agent_name", "")
        agent_id = self.agent_mapping.get(agent_name, agent_name.lower())

        # Update agent status to completed
        task_manager.update_agent_status(
            task_id=self.task_id,
            agent_id=agent_id,
            new_status="completed",
            progress=100.0
        )

        # Mark data flow as completed
        self._complete_data_flow(agent_id)

        # Update overall progress
        progress = self._calculate_overall_progress(agent_id)
        task_manager.update_task_processing_status(
            task_id=self.task_id,
            new_status="processing",
            progress=progress,
            current_agent_id=agent_id
        )

        # Add timeline event
        task_manager.add_timeline_event(
            task_id=self.task_id,
            event_type="agent_completed",
            message=f"{agent_name} completed successfully",
            agent_id=agent_id
        )

        logger.info(f"Agent {agent_name} completed for task {self.task_id}")

    async def _handle_agent_error(self, event: Dict[str, Any]) -> None:
        """Handle agent error event."""
        agent_name = event.get("agent_name", "")
        agent_id = self.agent_mapping.get(agent_name, agent_name.lower())
        error_message = event.get("error", "Unknown error")

        # Update agent status to error
        task_manager.update_agent_status(
            task_id=self.task_id,
            agent_id=agent_id,
            new_status="error",
            progress=self.agent_progress.get(agent_id, 0)
        )

        # Add error log
        task_manager.add_agent_log(
            task_id=self.task_id,
            agent_id=agent_id,
            level="error",
            message=error_message
        )

        logger.error(f"Agent {agent_name} error for task {self.task_id}: {error_message}")

    async def _handle_log_event(self, event: Dict[str, Any]) -> None:
        """Handle log events from ADK."""
        agent_name = event.get("agent_name", "")
        agent_id = self.agent_mapping.get(agent_name, agent_name.lower())
        level = event.get("level", "info").lower()
        message = event.get("message", "")

        if agent_id and message:
            task_manager.add_agent_log(
                task_id=self.task_id,
                agent_id=agent_id,
                level=level,
                message=message
            )

    async def _handle_tool_event(self, event: Dict[str, Any]) -> None:
        """Handle tool execution events."""
        tool_name = event.get("tool_name", "")
        agent_name = event.get("agent_name", "")
        agent_id = self.agent_mapping.get(agent_name, agent_name.lower())

        if agent_id:
            # Update agent progress based on tool execution
            current_progress = self.agent_progress.get(agent_id, 0)
            new_progress = min(current_progress + 20, 90)  # Cap at 90% until completion
            self.agent_progress[agent_id] = new_progress

            task_manager.update_agent_status(
                task_id=self.task_id,
                agent_id=agent_id,
                new_status="running",
                progress=new_progress
            )

            # Log tool execution
            task_manager.add_agent_log(
                task_id=self.task_id,
                agent_id=agent_id,
                level="info",
                message=f"Executing tool: {tool_name}"
            )

    async def _handle_message_event(self, event: Dict[str, Any]) -> None:
        """Handle message events from agents."""
        agent_name = event.get("agent_name", "")
        agent_id = self.agent_mapping.get(agent_name, agent_name.lower())
        content = event.get("content", "")

        if agent_id and content:
            # Extract meaningful updates from agent messages
            if "progress" in content.lower():
                # Try to parse progress updates
                task_manager.add_agent_log(
                    task_id=self.task_id,
                    agent_id=agent_id,
                    level="info",
                    message=content[:200]  # Truncate long messages
                )

    def _update_data_flows(self, current_agent_id: str) -> None:
        """Update data flow statuses based on current agent."""
        flow_sequence = [
            ("youtube-node", "transcript-fetcher"),
            ("transcript-fetcher", "summarizer-agent"),
            ("summarizer-agent", "synthesizer-agent"),
            ("synthesizer-agent", "audio-generator"),
            ("audio-generator", "ui-player")
        ]

        for from_agent, to_agent in flow_sequence:
            if to_agent == current_agent_id:
                task_manager.update_data_flow_status(
                    self.task_id, from_agent, to_agent, "transferring"
                )
                break

    def _complete_data_flow(self, completed_agent_id: str) -> None:
        """Mark data flows as completed."""
        flow_mapping = {
            "transcript-fetcher": ("youtube-node", "transcript-fetcher"),
            "summarizer-agent": ("transcript-fetcher", "summarizer-agent"),
            "synthesizer-agent": ("summarizer-agent", "synthesizer-agent"),
            "audio-generator": ("synthesizer-agent", "audio-generator")
        }

        if completed_agent_id in flow_mapping:
            from_agent, to_agent = flow_mapping[completed_agent_id]
            task_manager.update_data_flow_status(
                self.task_id, from_agent, to_agent, "completed"
            )

    def _calculate_overall_progress(self, current_agent_id: str) -> int:
        """Calculate overall task progress based on agent completion."""
        progress_mapping = {
            "transcript-fetcher": 25,
            "summarizer-agent": 50,
            "synthesizer-agent": 75,
            "audio-generator": 90
        }
        return progress_mapping.get(current_agent_id, 0)
```

#### 4.2 Update ADK Pipeline Runner with WebSocket Support

**Update**: `src/adk_runners/pipeline_runner.py`

```python
# Add to imports
from .websocket_bridge import AdkWebSocketBridge

# Update the run_async method in AdkPipelineRunner class
async def run_async(self, video_ids: List[str], output_dir: str, task_id: Optional[str] = None) -> Dict[str, Any]:
    """Run the complete pipeline using ADK with WebSocket support.

    Args:
        video_ids: List of YouTube video IDs to process
        output_dir: Directory for final audio output
        task_id: Optional task ID for WebSocket updates

    Returns:
        Dictionary containing results and status information
    """
    logger.info(f"Starting ADK pipeline for {len(video_ids)} videos")

    # Initialize WebSocket bridge if task_id provided
    ws_bridge = None
    if task_id:
        ws_bridge = AdkWebSocketBridge(task_id)

        # Set initial agent statuses
        from src.core import task_manager
        initial_agents = ["transcript-fetcher", "summarizer-agent", "synthesizer-agent", "audio-generator"]
        for agent_id in initial_agents:
            task_manager.update_agent_status(
                task_id=task_id,
                agent_id=agent_id,
                new_status="pending",
                progress=0.0
            )

    try:
        # Create session
        session = await self.session_service.create_session(
            state={"video_ids": video_ids, "output_dir": output_dir},
            app_name='podcast_digest_app',
            user_id='system_user'
        )

        # Prepare input message
        input_message = f"Process YouTube videos with IDs: {video_ids}"

        # Run the agent and process events
        events = []
        async for event in self.runner.run_async(
            session_id=session.id,
            user_id=session.user_id,
            new_message={"role": "user", "content": input_message}
        ):
            events.append(event)
            logger.info(f"Received event: {event}")

            # Send WebSocket updates if bridge is available
            if ws_bridge:
                await ws_bridge.process_adk_event(event)

        # Extract results from session state or events
        final_audio_path = session.state.get("final_audio_path")
        dialogue_script = session.state.get("dialogue_script", [])
        summaries = session.state.get("summaries", [])

        if final_audio_path:
            # Mark final data flow and task as completed
            if task_id:
                task_manager.update_data_flow_status(
                    task_id, "audio-generator", "ui-player", "completed"
                )

                # Extract summary from dialogue
                summary_text = self._create_summary_from_dialogue(dialogue_script)

                # Create audio URL
                from pathlib import Path
                audio_filename = Path(final_audio_path).name
                audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}"

                # Mark task completed
                task_manager.set_task_completed(task_id, summary_text, audio_url)

            return {
                "status": "success",
                "success": True,
                "final_audio_path": final_audio_path,
                "dialogue_script": dialogue_script,
                "summary_count": len(summaries) if isinstance(summaries, list) else 0,
                "transcript_count": len(video_ids),
                "failed_transcripts": [],
                "error": None
            }
        else:
            error_msg = "Pipeline completed but no audio file was generated"
            if task_id:
                task_manager.set_task_failed(task_id, error_msg)
            return self._error_result(error_msg, video_ids)

    except Exception as e:
        logger.exception(f"ADK Pipeline error: {e}")
        if task_id:
            task_manager.set_task_failed(task_id, str(e))
        return self._error_result(f"Pipeline error: {e}", video_ids)

def _create_summary_from_dialogue(self, dialogue_script: List[Dict[str, str]]) -> str:
    """Create summary text from dialogue script."""
    if not dialogue_script:
        return "ADK Generated Summary"

    summary_lines = []
    for item in dialogue_script[:3]:  # Take first 3 lines
        speaker = item.get('speaker', '')
        line = item.get('line', '')
        if line:
            summary_lines.append(f"{speaker}: {line}")

    return "ADK Generated Summary: " + " | ".join(summary_lines) if summary_lines else "ADK Generated Summary"
```

#### 4.3 Update API Endpoint to Pass task_id

**Update**: `src/api/v1/endpoints/tasks.py` (modify the run_adk_processing_pipeline function)

```python
async def run_adk_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """Run the ADK-based processing pipeline with WebSocket support."""
    logger.info(f"Starting ADK pipeline for task {task_id}")

    try:
        # Extract video ID
        youtube_url = str(request_data.youtube_url)
        video_id = extract_video_id_from_url(youtube_url)

        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")

        # Update task status
        task_manager.update_task_processing_status(
            task_id,
            "processing",
            progress=5,
            current_agent_id="transcript-fetcher"
        )

        # Run ADK pipeline with task_id for WebSocket updates
        adk_pipeline = AdkPipelineRunner()
        result = await adk_pipeline.run_async(
            video_ids=[video_id],
            output_dir=settings.OUTPUT_AUDIO_DIR,
            task_id=task_id  # Pass task_id for WebSocket bridge
        )

        # Results handling remains the same
        # The WebSocket updates are now handled within the pipeline

    except Exception as e:
        logger.error(f"Error in ADK pipeline for task {task_id}: {e}", exc_info=True)
        task_manager.set_task_failed(task_id, str(e))
```

### Phase 5: ADK Integration and Testing (2 days)

#### 4.1 Create ADK Runner

**New file**: `src/adk_runners/pipeline_runner.py`

```python
"""
ADK-based pipeline runner for podcast digest generation.
"""
import logging
import os
from typing import List, Dict, Any

# ADK imports
from google.adk.runners import Runner
from google.adk.runtime.sessions import InMemorySessionService
from google.adk.runtime.artifacts import InMemoryArtifactService

from ..adk_agents import root_agent

logger = logging.getLogger(__name__)

class AdkPipelineRunner:
    """ADK-based pipeline runner."""

    def __init__(self):
        """Initialize ADK runner with services."""
        self.session_service = InMemorySessionService()
        self.artifact_service = InMemoryArtifactService()

        self.runner = Runner(
            agent=root_agent,
            session_service=self.session_service,
            artifact_service=self.artifact_service
        )

        logger.info("ADK Pipeline Runner initialized")

    async def run_async(self, video_ids: List[str], output_dir: str) -> Dict[str, Any]:
        """Run the complete pipeline using ADK.

        Args:
            video_ids: List of YouTube video IDs to process
            output_dir: Directory for final audio output

        Returns:
            Dictionary containing results and status information
        """
        logger.info(f"Starting ADK pipeline for {len(video_ids)} videos")

        try:
            # Create session
            session = await self.session_service.create_session(
                state={"video_ids": video_ids, "output_dir": output_dir},
                app_name='podcast_digest_app',
                user_id='system_user'
            )

            # Prepare input message
            input_message = f"Process YouTube videos with IDs: {video_ids}"

            # Run the agent
            events = []
            async for event in self.runner.run_async(
                session_id=session.id,
                user_id=session.user_id,
                new_message={"role": "user", "content": input_message}
            ):
                events.append(event)
                logger.info(f"Received event: {event}")

            # Extract results from session state or events
            final_audio_path = session.state.get("final_audio_path")
            dialogue_script = session.state.get("dialogue_script", [])
            summaries = session.state.get("summaries", [])

            if final_audio_path:
                return {
                    "status": "success",
                    "success": True,
                    "final_audio_path": final_audio_path,
                    "dialogue_script": dialogue_script,
                    "summary_count": len(summaries) if isinstance(summaries, list) else 0,
                    "transcript_count": len(video_ids),
                    "failed_transcripts": [],
                    "error": None
                }
            else:
                return self._error_result(
                    "Pipeline completed but no audio file was generated",
                    video_ids
                )

        except Exception as e:
            logger.exception(f"ADK Pipeline error: {e}")
            return self._error_result(f"Pipeline error: {e}", video_ids)

    def _error_result(self, error_msg: str, video_ids: List[str]) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "status": "error",
            "success": False,
            "final_audio_path": None,
            "dialogue_script": [],
            "summary_count": 0,
            "transcript_count": 0,
            "failed_transcripts": video_ids,
            "error": error_msg
        }

    def run_pipeline(self, video_ids: List[str], output_dir: str = "./output_audio") -> Dict[str, Any]:
        """Synchronous wrapper for the async pipeline."""
        import asyncio
        return asyncio.run(self.run_async(video_ids, output_dir))
```

#### 4.2 Create Test Suite

**New file**: `tests/test_adk_migration.py`

```python
"""
Tests for ADK migration components.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from src.adk_agents import root_agent
from src.adk_runners.pipeline_runner import AdkPipelineRunner
from src.adk_tools.transcript_tools import fetch_youtube_transcript

class TestAdkMigration:
    """Test suite for ADK migration."""

    def test_agent_initialization(self):
        """Test that ADK agents initialize correctly."""
        assert root_agent.name == "PodcastDigestCoordinator"
        assert root_agent.model == "gemini-2.5-flash-preview-04-17"
        assert len(root_agent.sub_agents) == 4

    def test_transcript_tool(self):
        """Test transcript tool functionality."""
        with patch('src.adk_tools.transcript_tools.YouTubeTranscriptApi') as mock_api:
            # Mock successful transcript
            mock_api.get_transcript.return_value = [
                {"text": "Hello world", "start": 0.0, "duration": 2.0}
            ]

            result = fetch_youtube_transcript("test_video_id")

            assert result["success"] is True
            assert result["video_id"] == "test_video_id"
            assert "Hello world" in result["transcript"]

    @pytest.mark.asyncio
    async def test_pipeline_runner_initialization(self):
        """Test ADK pipeline runner initialization."""
        runner = AdkPipelineRunner()

        assert runner.runner is not None
        assert runner.session_service is not None
        assert runner.artifact_service is not None

    def test_agent_structure(self):
        """Test that agent structure matches ADK patterns."""
        # Verify sub-agents
        sub_agent_names = {agent.name for agent in root_agent.sub_agents}
        expected_names = {
            "TranscriptFetcher",
            "SummarizerAgent",
            "DialogueSynthesizer",
            "AudioGenerator"
        }

        assert sub_agent_names == expected_names
```

### Phase 5: API Integration (1 day)

#### 5.1 Update API Endpoints

**Modify**: `src/api/v1/endpoints/tasks.py`

```python
# Replace existing pipeline import
# from src.runners.simple_pipeline import SimplePipeline

# With ADK pipeline import
from src.adk_runners.pipeline_runner import AdkPipelineRunner

# Update the processing function to use ADK
async def run_adk_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """Run the ADK-based processing pipeline."""
    logger.info(f"Starting ADK pipeline for task {task_id}")

    try:
        # Extract video ID
        youtube_url = str(request_data.youtube_url)
        video_id = extract_video_id_from_url(youtube_url)

        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")

        # Update task status
        task_manager.update_task_processing_status(
            task_id,
            "processing",
            progress=5,
            current_agent_id="transcript-fetcher"
        )

        # Run ADK pipeline
        adk_pipeline = AdkPipelineRunner()
        result = await adk_pipeline.run_async(
            video_ids=[video_id],
            output_dir=settings.OUTPUT_AUDIO_DIR
        )

        # Process results
        if result.get("success"):
            final_audio_path = result.get("final_audio_path")
            if final_audio_path:
                # Create audio URL
                audio_filename = Path(final_audio_path).name
                audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}"

                # Create summary from dialogue
                dialogue_script = result.get("dialogue_script", [])
                summary_lines = []
                for item in dialogue_script[:3]:
                    speaker = item.get('speaker', '')
                    line = item.get('line', '')
                    if line:
                        summary_lines.append(f"{speaker}: {line}")

                summary_text = "ADK Generated Summary: " + " | ".join(summary_lines)

                # Mark task completed
                task_manager.set_task_completed(task_id, summary_text, audio_url)
                logger.info(f"ADK pipeline completed successfully for task {task_id}")
            else:
                raise ValueError("ADK pipeline succeeded but no audio file was generated")
        else:
            error_message = result.get("error", "Unknown ADK pipeline error")
            task_manager.set_task_failed(task_id, error_message)

    except Exception as e:
        logger.error(f"Error in ADK pipeline for task {task_id}: {e}", exc_info=True)
        task_manager.set_task_failed(task_id, str(e))

# Update endpoint to use ADK pipeline
# Replace: background_tasks.add_task(run_real_processing_pipeline, ...)
# With:
background_tasks.add_task(run_adk_processing_pipeline, task_details["task_id"], request)
```

#### 5.2 Update Requirements

```bash
# Add ADK to requirements.txt
echo "google-adk>=1.0.0" >> requirements.txt
```

### Phase 6: Deployment Configuration (1 day)

#### 6.1 Cloud Run Deployment

**New file**: `deployment/cloud_run/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY podcast-digest-ui/build ./static/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "-m", "src.main"]
```

**New file**: `deployment/cloud_run/deploy.sh`

```bash
#!/bin/bash

# Cloud Run deployment script for ADK-based agent

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
REGION=${GOOGLE_CLOUD_LOCATION:-us-central1}
SERVICE_NAME="podcast-digest-adk"

echo "Deploying to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_GENAI_USE_VERTEXAI=true" \
    --memory 2Gi \
    --cpu 2 \
    --timeout 900 \
    --max-instances 10

echo "✅ Deployment completed successfully!"
```

#### 6.2 Vertex AI Agent Engine Deployment

**New file**: `deployment/agent_engine/deploy.py`

```python
"""
Deploy ADK agent to Vertex AI Agent Engine.
"""
import os
import vertexai
from vertexai.preview import reasoning_engines
from src.adk_agents import root_agent

def deploy_to_agent_engine():
    """Deploy the ADK agent to Vertex AI Agent Engine."""

    # Initialize Vertex AI
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    vertexai.init(project=project_id, location=location)

    # Wrap agent for Agent Engine
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True
    )

    # Deploy to Agent Engine
    print("Deploying to Vertex AI Agent Engine...")
    remote_app = vertexai.agent_engines.create(
        agent_engine=app,
        requirements=["google-adk>=1.0.0", "google-cloud-aiplatform[adk,agent_engines]"]
    )

    print(f"✅ Deployed successfully!")
    print(f"Resource name: {remote_app.resource_name}")

    return remote_app

if __name__ == "__main__":
    deploy_to_agent_engine()
```

### Phase 7: Testing and Validation (2 days)

#### 7.1 Comprehensive Testing

```bash
# Run ADK-specific tests
pytest tests/test_adk_migration.py -v

# Test with ADK CLI
cd src/adk_agents
adk web  # Test in ADK web interface

# Test complete pipeline
python -c "
from src.adk_runners.pipeline_runner import AdkPipelineRunner
runner = AdkPipelineRunner()
result = runner.run_pipeline(['dQw4w9WgXcQ'])  # Rick Roll test
print('✅ Pipeline test completed:', result['success'])
"
```

#### 7.2 Migration Validation

Create validation script to ensure feature parity:

**File**: `migration_validation.py`

```python
"""
Validate ADK migration maintains all functionality.
"""
import asyncio
from src.adk_runners.pipeline_runner import AdkPipelineRunner
from src.runners.simple_pipeline import SimplePipeline

async def validate_migration():
    """Compare old vs new pipeline results."""

    test_video_id = "dQw4w9WgXcQ"  # Rick Roll for testing

    print("🔄 Testing ADK pipeline...")
    adk_runner = AdkPipelineRunner()
    adk_result = await adk_runner.run_async([test_video_id], "./test_output")

    print("🔄 Testing original pipeline...")
    original_runner = SimplePipeline()
    original_result = await original_runner.run_async([test_video_id], "./test_output")

    # Compare results
    adk_success = adk_result.get("success", False)
    original_success = original_result.get("success", False)

    print(f"ADK Result: {adk_success}")
    print(f"Original Result: {original_success}")

    if adk_success == original_success:
        print("✅ Migration validation PASSED - functionality maintained")
    else:
        print("❌ Migration validation FAILED - functionality differs")

    return adk_success == original_success

if __name__ == "__main__":
    asyncio.run(validate_migration())
```

## Migration Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 1 – Env setup & PoC | 1 day | ADK installed; hello-world agent validated |
| 2 – Minimal wrapper | 1 day | Single-agent wrapper + `@tool`s; all tests green |
| 3 – Create ADK agents | 2 days | ADK agents implementing complete pipeline |
| 4 – WebSocket integration | 1 day | Real-time updates via WebSocket bridge |
| 5 – API integration | 1 day | FastAPI endpoints using ADK pipeline |
| 6 – Testing & validation | 2 days | End-to-end parity checks, comprehensive testing |
| 7 – Deployment | 1 day | Cloud Run & Agent Engine deployment |
| 8 – Buffer / bug-fix | 1 day | Unexpected issues, docs update |
| **Total** | **10 days** | **ADK adoption with full feature parity** |

## Risk Mitigation

### High-Priority Risks

1. **ADK Learning Curve** - New architecture patterns
   - **Mitigation**: Phase 1 focuses on understanding real ADK patterns
   - **Fallback**: Keep original implementation running in parallel

2. **Tool Conversion Complexity** - Different tool paradigms
   - **Mitigation**: Phase 2 creates comprehensive tool mapping
   - **Fallback**: Gradual tool migration with testing

3. **Session Management Changes** - ADK handles sessions differently
   - **Mitigation**: Use ADK built-in session management
   - **Fallback**: Implement session compatibility layer if needed

4. **Deployment Dependencies** - Additional Google Cloud setup
   - **Mitigation**: Phase 6 includes complete deployment documentation
   - **Fallback**: Cloud Run deployment as simpler alternative

### Success Criteria

- ✅ All existing functionality preserved
- ✅ ADK agents implement complete pipeline
- ✅ API endpoints work identically
- ✅ Deployment to Cloud Run successful
- ✅ Performance same or better than current implementation
- ✅ Migration validation tests pass

## Post-Migration Benefits

1. **Production-Ready Architecture** - Using Google's official framework
2. **Built-in Monitoring** - ADK provides comprehensive observability
3. **Simplified Deployment** - Official Cloud Run and Agent Engine support
4. **Community Support** - Access to ADK ecosystem and examples
5. **Future Compatibility** - Aligned with Google's AI agent roadmap

## Conclusion

This migration represents a complete architectural shift to leverage Google's official ADK v1.0.0. The comprehensive approach ensures we avoid the compatibility issues that caused previous migration attempts to fail, while establishing a solid foundation for future development.
