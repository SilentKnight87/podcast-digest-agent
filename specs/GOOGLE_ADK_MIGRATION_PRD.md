# Google Agent Development Kit (ADK) Migration PRD

## Status: 📝 PRD UPDATED

**Completion Date**: N/A
**Priority**: Medium  
**Estimated Time**: 4-5 days (increased to include test migration)
**Actual Time**: N/A
**Dependencies**: Backend cleanup (COMPLETED)

### Implementation Summary
- ✅ PRD updated to reflect Google Agent Development Kit (ADK) v1.0.0+ patterns
- ✅ Corrected import paths and class names for April 2025 release
- ✅ Added event streaming patterns (core ADK feature)
- ✅ Updated session management approach
- ✅ Included A2A protocol compliance
- ✅ Added comprehensive test migration requirements
- ☐ Implementation not started

### Deviations from Original Spec
- **Event Streaming**: Added async event streaming pattern (core to ADK v1.0.0+)
- **Session Management**: Updated to use `InMemorySessionService` instead of direct Session instantiation
- **Agent Class**: Clarified that `Agent` and `LlmAgent` are interchangeable
- **Message Format**: Changed from plain strings to `UserContent` with `Part` objects
- **Tool Patterns**: Simplified tool creation - plain functions work without `FunctionTool` wrapper
- **Timeline**: Increased estimate by 1 day to account for event streaming complexity
- **Test Migration**: Added comprehensive test updates as integral part of ADK migration

### Prerequisites
- ✅ Backend cleanup completed
- ☐ Google Agent Development Kit (ADK) installed (v1.0.0+ for Python)
- ☐ ADK documentation reviewed (google.github.io/adk-docs/)
- ☐ Test environment prepared
- ☐ Understanding of event streaming patterns
- ☐ A2A protocol familiarity
- ☐ All existing tests reviewed for ADK compatibility
- ☐ Google Cloud credentials configured (for TTS)
- ☐ Python 3.9+ installed

### Junior Engineer Checklist
Before starting, ensure you understand:
- [ ] Basic async/await in Python
- [ ] How generators work (`yield`)
- [ ] What event streaming means
- [ ] Basic testing with pytest
- [ ] Git branching for safe implementation

---

## Overview

This specification outlines the migration of the podcast digest backend from custom agent implementation to Google's Agent Development Kit (ADK) architecture and patterns. ADK was released in April 2025 at Google Cloud NEXT 2025 as an open-source framework for building multi-agent AI systems. The main objective is to learn ADK while building a production-ready system using the same tools Google uses internally for products like Agentspace and Customer Engagement Suite.

### What is ADK?
The Agent Development Kit (ADK) is Google's framework that makes "agent development feel more like software development." It provides:
- **Code-first approach**: Define agents in Python/Java code
- **Model-agnostic**: Works with Gemini, GPT-4, Claude, and more
- **Production-ready**: Used internally at Google for Agentspace
- **Multi-agent support**: Build complex agent systems easily

### Official Resources
- 📚 **Documentation**: https://google.github.io/adk-docs/
- 🐍 **Python SDK**: https://github.com/google/adk-python
- 📦 **Sample Agents**: https://github.com/google/adk-samples
- 💬 **Community**: Join the ADK Discord for support

## Goals

1. Replace custom agent implementation with Google Agent Development Kit (ADK) components
2. Learn and implement ADK patterns and best practices from the April 2025 release
3. Use ADK's built-in session state management and event streaming system
4. Maintain all existing functionality during migration
5. Improve system architecture with proper ADK patterns
6. Migrate ALL existing tests to use ADK testing patterns
7. Provide excellent learning opportunities for ADK development

## Implementation Details

### Prerequisites

Before starting the migration, ensure proper setup of the Google ADK environment.

#### 1. Install Google ADK

```bash
# Navigate to project root
cd /Users/peterbrown/Documents/Code/podcast-digest-agent

# Create a new branch for ADK migration
git checkout -b feature/adk-migration

# Activate virtual environment
source venv/bin/activate

# Install Google Agent Development Kit
pip install google-adk[all]

# Add to requirements.txt
echo "google-adk[all]>=1.0.0" >> requirements.txt

# For deployment to Vertex AI Agent Engine
echo "vertexai>=1.0.0" >> requirements.txt

# Install dependencies
pip install -r requirements.txt
```

**Troubleshooting**:
- If installation fails, try: `pip install --upgrade pip`
- For M1 Macs: `pip install --no-binary :all: google-adk[all]`
- Check Python version: `python --version` (must be 3.9+)

#### 2. Verify ADK Installation

```bash
# Test basic ADK import (April 2025 release)
python -c "
from google.adk.agents import Agent, LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.tools import FunctionTool, agent_tool
from google.adk.sessions import Session, InMemorySessionService
from google.adk.runners import Runner, InMemoryRunner
from google.adk.events import Event
from google.genai.types import Content, Part
print('✅ Google Agent Development Kit v1.0.0+ installed successfully')
print('✅ ADK April 2025 release - All required components available')
print('✅ Ready to build multi-agent systems like Agentspace!')
"
```

#### 3. Study ADK Patterns

Review the key Agent Development Kit patterns from the April 2025 release:

##### Core Agent Types
- **Agent/LlmAgent**: LLM-powered agents that process data and make decisions
  - `Agent` and `LlmAgent` are aliases - use either
  - Requires: name, model, instruction
  - Optional: tools, output_key, description
  
- **SequentialAgent**: Workflow agent that chains sub-agents in sequence
  - Runs agents one after another
  - Each agent can access previous agent's output via state
  
- **ParallelAgent**: Workflow agent that runs multiple sub-agents simultaneously
  - Executes agents concurrently for speed
  - Useful for independent tasks
  
- **LoopAgent**: Workflow agent for iterative processing with conditions
  - Repeats agents until condition met
  - Has max_iterations safety limit

##### Tool Patterns
- **FunctionTool**: Wrap Python functions as ADK tools (optional)
  - Plain functions work as tools directly
  - Use FunctionTool for advanced features
  
- **AgentTool**: Wrap other agents as tools for hierarchical design
  - Allows agents to call other agents
  - Enables complex multi-agent systems

##### Execution Patterns  
- **Session State**: Persistent state management across agent interactions
  - Dictionary-like storage shared between agents
  - Updated via session service
  
- **Runner/InMemoryRunner**: Execute agents with event streaming
  - InMemoryRunner for testing/development
  - Runner for production with external services
  
- **Event Streaming**: Real-time processing with async generators
  - Events flow as agents execute
  - Can track progress and intermediate results

### Phase 1: Create ADK Tool Wrappers (1 day)

Transform existing tools to be ADK-compatible. In ADK, tools are just Python functions - no special wrappers required for basic usage!

**Key Concept**: ADK automatically converts Python functions to tools. The function's:
- Name becomes the tool name
- Docstring becomes the tool description  
- Parameters become the tool's input schema
- Return value becomes the tool's output

#### Create ADK Tools File

**New file**: `/src/tools/adk_tools.py`

```python
"""
Agent Development Kit (ADK) compatible tools for the podcast digest pipeline.
Using ADK patterns from April 2025 release.
"""
import json
import tempfile
import asyncio
from typing import List, Dict, Any
from pathlib import Path
from google.adk.tools import FunctionTool
from google.cloud import texttospeech_v1

# Import existing tools - make sure these exist!
from .transcript_tools import fetch_transcripts
from .audio_tools import generate_audio_segment_tool, combine_audio_segments_tool

# Note for Junior Engineers:
# These imports reference your existing tools in the codebase
# Make sure the paths are correct relative to this file
# If imports fail, check that the files exist and __init__.py is present

def fetch_youtube_transcripts(video_ids: List[str]) -> Dict[str, Any]:
    """
    ADK tool for fetching YouTube transcripts.
    
    This docstring is IMPORTANT - ADK uses it as the tool description!
    
    Args:
        video_ids: List of YouTube video IDs to process
        
    Returns:
        Dictionary mapping video IDs to transcript results
        
    Example:
        result = fetch_youtube_transcripts(["dQw4w9WgXcQ"])
        # Returns: {"dQw4w9WgXcQ": "Never gonna give you up..."}
    """
    # ADK tools can be sync or async - Runner handles both
    return fetch_transcripts.run(video_ids=video_ids)

async def generate_audio_segments(
    dialogue_script: str, 
    temp_dir: str, 
    tts_client: Any
) -> List[str]:
    """
    ADK tool wrapper for generating audio segments from dialogue.
    
    Args:
        dialogue_script: JSON string containing dialogue script
        temp_dir: Temporary directory for audio segments
        tts_client: Google Cloud TTS client
        
    Returns:
        List of generated audio segment file paths
    """
    try:
        dialogue = json.loads(dialogue_script)
        segment_files = []
        
        # Generate audio segments concurrently
        tasks = []
        for i, segment in enumerate(dialogue):
            speaker = segment.get("speaker", "A")
            line = segment.get("line", "")
            
            if line:
                output_path = Path(temp_dir) / f"segment_{i:03d}_{speaker}.mp3"
                task = generate_audio_segment_tool.run(
                    text=line,
                    speaker=speaker,
                    output_filepath=str(output_path),
                    tts_client=tts_client
                )
                tasks.append(task)
        
        # Wait for all segments to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect successful results
        for result in results:
            if isinstance(result, str):  # Success case
                segment_files.append(result)
            else:  # Exception case
                print(f"Error generating segment: {result}")
        
        return segment_files
        
    except json.JSONDecodeError as e:
        print(f"Error parsing dialogue script: {e}")
        return []
    except Exception as e:
        print(f"Error generating audio segments: {e}")
        return []

async def combine_audio_files(segment_files: List[str], output_dir: str) -> str:
    """
    ADK tool wrapper for combining audio segments into final audio.
    
    Args:
        segment_files: List of audio segment file paths
        output_dir: Directory for final audio output
        
    Returns:
        Path to the combined audio file
    """
    try:
        return await combine_audio_segments_tool.run(
            segment_filepaths=segment_files,
            output_dir=output_dir
        )
    except Exception as e:
        print(f"Error combining audio files: {e}")
        return ""

# ADK Tool Creation - Three Ways:

# Method 1: Direct function (RECOMMENDED for simplicity)
transcript_tool = fetch_youtube_transcripts
audio_generation_tool = generate_audio_segments  
audio_combination_tool = combine_audio_files

# Method 2: Using FunctionTool for more control (OPTIONAL)
# from google.adk.tools import FunctionTool
# transcript_tool = FunctionTool(
#     func=fetch_youtube_transcripts,
#     name="fetch_transcripts",  # Override function name
#     description="Fetches YouTube video transcripts"  # Override docstring
# )

# Method 3: Using decorators (OPTIONAL)
# from google.adk.tools import tool
# @tool(name="fetch_transcripts")
# def fetch_youtube_transcripts(video_ids: List[str]) -> Dict[str, Any]:
#     ...

# Junior Engineer Note: Start with Method 1 - it's the simplest!
```

### Phase 2: Create ADK Agents (2 days)

Replace custom agents with ADK Agent implementations. This is the core of the migration!

**Understanding ADK Agents**:
1. Agents are configured with instructions (like system prompts)
2. They have access to tools (functions they can call)
3. They share data through session state
4. They emit events as they process

**Agent Lifecycle**:
1. Agent receives input message
2. Agent thinks using its LLM
3. Agent may call tools
4. Agent updates session state
5. Agent returns response

#### Create ADK Agents File

**New file**: `/src/agents/adk_agents.py`

```python
"""
Google Agent Development Kit (ADK) agents for podcast digest pipeline.
Implemented using ADK v1.0.0+ patterns from April 2025 release.
"""
from google.adk.agents import Agent, LlmAgent, SequentialAgent
from google.adk.tools import agent_tool, FunctionTool
from google.genai.types import Content, Part

# Import ADK tools
from ..tools.adk_tools import (
    transcript_tool, 
    audio_generation_tool, 
    audio_combination_tool
)

# Individual ADK Agent Definitions
# Note: Agent and LlmAgent are the same class - use either name

# Step 1: Create the transcript fetcher agent
transcript_agent = Agent(
    name="TranscriptFetcher",
    model="gemini-2.0-flash",
    description="Fetches YouTube video transcripts and stores them in session state",
    instruction="""
    You are a transcript fetcher agent. Your job is to:
    
    1. Take YouTube video IDs from the user input
    2. Use the fetch_youtube_transcripts tool to get transcripts
    3. Store successful transcripts in the session state
    4. Report any failures or issues
    
    Always be thorough in your transcript fetching and provide clear status updates.
    
    IMPORTANT: The video IDs are already in the session state under 'video_ids' key.
    """,
    tools=[transcript_tool],
    output_key="transcripts"  # ADK will automatically save output to session state
)

summarizer_agent = Agent(
    name="SummarizerAgent",
    model="gemini-2.0-flash",
    description="Summarizes podcast transcripts into concise, informative summaries",
    instruction="""
    You are an expert podcast summarizer. Your role is to:
    
    1. Read transcripts from the session state key 'transcripts'
    2. Generate concise yet comprehensive summaries for each transcript
    3. Focus on key topics, main discussions, and important conclusions
    4. Preserve the most valuable insights and information
    5. Save your summaries to the session state
    
    Create summaries that capture the essence while being engaging and informative.
    Aim for summaries that are 10-15% of the original transcript length.
    """,
    output_key="summaries"  # Save summaries to session state
)

synthesizer_agent = Agent(
    name="DialogueSynthesizer",
    model="gemini-2.0-flash", 
    description="Converts summaries into natural conversational dialogue scripts",
    instruction="""
    You are a dialogue synthesizer. Your task is to:
    
    1. Read summaries from session state key 'summaries'
    2. Create natural, engaging conversational dialogue between two speakers (A and B)
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
    output_key="dialogue_script"  # Save dialogue to session state
)

audio_agent = Agent(
    name="AudioGenerator",
    model="gemini-2.0-flash",
    description="Generates final audio files from dialogue scripts",
    instruction="""
    You are an audio generator. Your responsibilities are to:
    
    1. Read the dialogue script from session state key 'dialogue_script'
    2. Create a temporary directory for audio processing
    3. Use the generate_audio_segments tool to create individual audio segments
    4. Use the combine_audio_files tool to merge segments into final audio
    5. Save the final audio file path to session state
    
    Ensure high-quality audio generation with proper speaker differentiation.
    Handle any errors gracefully and provide clear status updates.
    """,
    tools=[audio_generation_tool, audio_combination_tool],
    output_key="final_audio_path"  # Save final audio path to session state
)

# Main ADK Pipeline Definition
# This chains our agents together in sequence!

podcast_pipeline = SequentialAgent(
    name="PodcastDigestPipeline",
    description="Complete end-to-end pipeline for generating podcast digests from YouTube URLs",
    sub_agents=[
        transcript_agent,     # Step 1: Fetch transcripts
        summarizer_agent,     # Step 2: Summarize content  
        synthesizer_agent,    # Step 3: Create dialogue
        audio_agent          # Step 4: Generate audio
    ]
)

# How it works:
# 1. transcript_agent runs first, saves transcripts to state['transcripts']
# 2. summarizer_agent reads state['transcripts'], saves summaries to state['summaries']
# 3. synthesizer_agent reads state['summaries'], saves dialogue to state['dialogue_script']
# 4. audio_agent reads state['dialogue_script'], generates audio, saves path to state['final_audio_path']

# Advanced ADK Patterns

# Parallel processing for multiple videos
from google.adk.agents import ParallelAgent

parallel_transcript_agent = ParallelAgent(
    name="ParallelTranscriptFetcher",
    description="Process multiple videos simultaneously",
    sub_agents=[transcript_agent]  # Runs transcript_agent for each video in parallel
)

# Hierarchical Agent Pattern (Agent as Tool)
from google.adk.tools import agent_tool

# Wrap agents as tools for use by other agents
transcript_tool = agent_tool.AgentTool(agent=transcript_agent)
summarizer_tool = agent_tool.AgentTool(agent=summarizer_agent)

# Iterative improvement pattern
from google.adk.agents import LoopAgent

quality_checker_agent = Agent(
    name="QualityChecker",
    model="gemini-2.0-flash",
    description="Evaluates summary quality and suggests improvements",
    instruction="""
    Evaluate the summary quality from session state key 'summaries'.
    Rate the quality as 'excellent', 'good', or 'needs_improvement'.
    If 'needs_improvement', provide specific suggestions.
    Save your assessment to session state key 'quality_assessment'.
    """,
    output_key="quality_assessment"
)

iterative_summary_pipeline = LoopAgent(
    name="IterativeSummaryRefiner",
    description="Iteratively improve summary quality",
    max_iterations=3,
    sub_agents=[
        summarizer_agent,
        quality_checker_agent
    ]
)
```

### Phase 3: Create ADK Pipeline Runner (1.5 days)

Replace the custom pipeline with an ADK-based runner that uses proper ADK patterns. This is where we tie everything together!

**Key Concepts**:
1. **InMemoryRunner**: Manages agent execution locally
2. **Session**: Stores state between agent calls
3. **Event Streaming**: Real-time updates as agents work
4. **Async/Await**: Non-blocking execution

#### Create ADK Pipeline Runner

**New file**: `/src/runners/adk_pipeline.py`

```python
"""
Agent Development Kit (ADK) based pipeline runner for podcast digest generation.
Implements event streaming and session management from ADK April 2025 release.
"""
import logging
import asyncio
import tempfile
from typing import List, Dict, Any, AsyncGenerator
from pathlib import Path

from google.adk.runners import Runner, InMemoryRunner
from google.adk.sessions import Session, InMemorySessionService
from google.adk.events import Event
from google.genai.types import Content, Part, UserContent
from google.cloud import texttospeech_v1

# Import ADK agents
from ..agents.adk_agents import podcast_pipeline

logger = logging.getLogger(__name__)

class AdkPipelineRunner:
    """
    ADK-based pipeline runner that orchestrates the complete podcast digest workflow.
    
    This class:
    1. Initializes the ADK runner with our pipeline
    2. Creates sessions for each processing job
    3. Streams events as agents work
    4. Returns the final results
    """
    
    def __init__(self):
        """Initialize the ADK pipeline runner."""
        # Use InMemoryRunner for local execution
        self.runner = InMemoryRunner(agent=podcast_pipeline)
        self.session_service = self.runner.session_service
        self.temp_dirs = []
        logger.info("ADK Pipeline Runner initialized")
    
    async def run_async(self, video_ids: List[str], output_dir: str) -> Dict[str, Any]:
        """
        Run the complete podcast digest pipeline using Google ADK.
        
        Args:
            video_ids: List of YouTube video IDs to process
            output_dir: Directory for final audio output
            
        Returns:
            Dictionary containing results and status information
        """
        logger.info(f"Starting ADK pipeline for {len(video_ids)} videos")
        
        try:
            # Initialize Google Cloud TTS client
            async with texttospeech_v1.TextToSpeechAsyncClient() as tts_client:
                # Create ADK session with initial state
                initial_state = {
                    "video_ids": video_ids,
                    "output_dir": output_dir,
                    "tts_client": tts_client
                }
                
                # Create session using session service
                session = await self.session_service.create_session(
                    app_name="podcast_digest_app",
                    user_id="system",
                    session_id=f"session_{asyncio.get_event_loop().time()}",
                    state=initial_state
                )
                
                # Create temporary directory for audio processing
                temp_dir = tempfile.mkdtemp(prefix="adk_podcast_segments_")
                self.temp_dirs.append(temp_dir)
                
                # Update session state
                await self.session_service.update_state(
                    app_name="podcast_digest_app",
                    user_id="system",
                    session_id=session.id,
                    state_delta={"temp_dir": temp_dir}
                )
                
                logger.info("ADK session initialized with state")
                
                # Prepare user message
                user_message = UserContent(
                    parts=[Part(text=f"Process YouTube videos with IDs: {video_ids}")]
                )
                
                # Run the ADK pipeline with event streaming
                logger.info("Starting ADK pipeline execution")
                final_audio_path = None
                dialogue_script = []
                summaries = []
                transcripts = {}
                
                # Stream events from the pipeline
                # This is the CORE PATTERN of ADK - async event streaming!
                async for event in self.runner.run_async(
                    user_id="system",
                    session_id=session.id,
                    new_message=user_message
                ):
                    # Each event represents something happening:
                    # - Agent thinking
                    # - Tool being called
                    # - State being updated
                    # - Final response
                    
                    if event.is_final_response():
                        logger.info(f"Final response from {event.author}")
                    
                    # Log intermediate results for debugging
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                logger.debug(f"Event from {event.author}: {part.text[:100]}...")
                    
                    # You could also:
                    # - Send progress updates to frontend
                    # - Save intermediate results
                    # - Handle errors in real-time
                
                # Get final session state after pipeline completion
                final_session = await self.session_service.get_session(
                    app_name="podcast_digest_app",
                    user_id="system",
                    session_id=session.id
                )
                
                # Extract results from final session state
                final_audio_path = final_session.state.get("final_audio_path")
                dialogue_script = final_session.state.get("dialogue_script", [])
                summaries = final_session.state.get("summaries", [])
                transcripts = final_session.state.get("transcripts", {})
                
                logger.info(f"ADK pipeline completed. Audio path: {final_audio_path}")
                
                # Process and return results
                if final_audio_path:
                    return {
                        "status": "success",
                        "success": True,
                        "dialogue_script": dialogue_script,
                        "final_audio_path": final_audio_path,
                        "summary_count": len(summaries) if isinstance(summaries, list) else 0,
                        "transcript_count": len(transcripts) if isinstance(transcripts, dict) else 0,
                        "failed_transcripts": [],
                        "error": None
                    }
                else:
                    return self._error_result(
                        "ADK pipeline completed but no audio file was generated", 
                        video_ids
                    )
                    
        except Exception as e:
            logger.exception(f"ADK Pipeline error: {e}")
            return self._error_result(f"ADK Pipeline error: {e}", video_ids)
        
        finally:
            # Clean up temporary directories
            self._cleanup()
    
    def _error_result(self, error_msg: str, video_ids: List[str]) -> Dict[str, Any]:
        """
        Create standardized error result dictionary.
        
        Args:
            error_msg: Error message to include
            video_ids: Video IDs that failed processing
            
        Returns:
            Standardized error result dictionary
        """
        return {
            "status": "error",
            "success": False,
            "dialogue_script": [],
            "final_audio_path": None,
            "summary_count": 0,
            "transcript_count": 0,
            "failed_transcripts": video_ids,
            "error": error_msg
        }
    
    def _cleanup(self):
        """Clean up temporary directories and resources."""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory {temp_dir}: {e}")
        
        self.temp_dirs.clear()
    
    def run_pipeline(self, video_ids: List[str], output_dir: str = "./output_audio") -> Dict[str, Any]:
        """
        Synchronous wrapper for the async ADK pipeline.
        
        Args:
            video_ids: List of YouTube video IDs to process
            output_dir: Directory for final audio output
            
        Returns:
            Pipeline execution results
        """
        logger.info("Running ADK pipeline synchronously")
        
        # For sync execution, use asyncio.run
        return asyncio.run(self.run_async(video_ids, output_dir))

# Advanced ADK Runner with Parallel Processing
class AdvancedAdkPipelineRunner(AdkPipelineRunner):
    """
    Advanced ADK pipeline runner with parallel processing capabilities.
    """
    
    async def run_parallel_async(
        self, 
        video_ids: List[str], 
        output_dir: str,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Run pipeline with parallel processing for multiple videos.
        
        Args:
            video_ids: List of YouTube video IDs to process
            output_dir: Directory for final audio output
            max_concurrent: Maximum number of concurrent processes
            
        Returns:
            Pipeline execution results
        """
        logger.info(f"Starting parallel ADK pipeline for {len(video_ids)} videos")
        
        # Split video IDs into batches for parallel processing
        batches = [
            video_ids[i:i + max_concurrent] 
            for i in range(0, len(video_ids), max_concurrent)
        ]
        
        all_results = []
        
        for batch in batches:
            # Process each batch in parallel
            batch_tasks = [
                self.run_async([video_id], output_dir) 
                for video_id in batch
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            all_results.extend(batch_results)
        
        # Combine results
        successful_results = [r for r in all_results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in all_results if not isinstance(r, dict) or not r.get("success")]
        
        return {
            "status": "completed",
            "success": len(successful_results) > 0,
            "total_processed": len(video_ids),
            "successful_count": len(successful_results),
            "failed_count": len(failed_results),
            "results": all_results
        }
```

### Phase 3.5: Create A2A Protocol File (15 minutes)

Create the Agent-to-Agent protocol compliance file for discoverability.

**Create**: `/.well-known/agent.json`

```json
{
  "name": "PodcastDigestAgent",
  "description": "Processes YouTube podcasts into audio digests using Google ADK",
  "version": "1.0.0",
  "capabilities": [
    "youtube-transcript-fetching",
    "content-summarization",
    "dialogue-generation",
    "audio-synthesis"
  ],
  "tools": [
    "fetch_youtube_transcripts",
    "generate_audio_segments",
    "combine_audio_files"
  ],
  "models": ["gemini-2.0-flash"],
  "framework": "google-adk",
  "framework_version": "1.0.0"
}
```

This file enables other agents to discover and potentially interact with your agent!

### Phase 4: Update API Integration (0.5 day)

Update the API endpoints to use the new ADK pipeline runner. This connects our new ADK pipeline to the existing API!

**What we're doing**:
1. Import the new ADK pipeline runner
2. Replace the old pipeline calls
3. Handle ADK results properly
4. Maintain backward compatibility

#### Update API Endpoints

**Modify**: `/src/api/v1/endpoints/tasks.py`

```python
# Replace the existing pipeline import
# from src.runners.pipeline_runner import PipelineRunner

# With ADK pipeline import
from src.runners.adk_pipeline import AdkPipelineRunner

# Update the processing function
async def run_adk_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """
    Run the ADK-based processing pipeline for podcast digest generation.
    
    Args:
        task_id: Unique identifier for the processing task
        request_data: Request data containing YouTube URL and options
    """
    logger.info(f"Starting ADK pipeline for task {task_id}")
    
    try:
        # Extract YouTube URL and convert to video ID
        youtube_url = str(request_data.youtube_url)
        video_id = extract_video_id_from_url(youtube_url)
        
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")
        
        # Update task manager with processing status
        task_manager.update_task_processing_status(
            task_id, 
            "processing", 
            progress=5, 
            current_agent_id="transcript-fetcher"
        )
        
        # Initialize and run ADK pipeline
        adk_pipeline = AdkPipelineRunner()
        result = await adk_pipeline.run_async(
            video_ids=[video_id], 
            output_dir=settings.OUTPUT_AUDIO_DIR
        )
        
        # Process results
        if result.get("success"):
            # Extract results from ADK pipeline
            final_audio_path = result.get("final_audio_path")
            dialogue_script = result.get("dialogue_script", [])
            
            if final_audio_path:
                # Get audio filename for URL
                audio_filename = Path(final_audio_path).name
                audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}"
                
                # Create summary text from dialogue script
                summary_lines = []
                for item in dialogue_script[:3]:  # First 3 dialogue lines
                    speaker = item.get('speaker', '')
                    line = item.get('line', '')
                    if line:
                        summary_lines.append(f"{speaker}: {line}")
                
                summary_text = "ADK Generated Summary: " + " | ".join(summary_lines)
                
                # Mark task as completed
                task_manager.set_task_completed(task_id, summary_text, audio_url)
                logger.info(f"ADK pipeline completed successfully for task {task_id}")
            else:
                raise ValueError("ADK pipeline succeeded but no audio file was generated")
        else:
            error_message = result.get("error", "Unknown ADK pipeline error")
            task_manager.set_task_failed(task_id, error_message)
            logger.error(f"ADK pipeline failed for task {task_id}: {error_message}")
            
    except Exception as e:
        logger.error(f"Error in ADK pipeline for task {task_id}: {e}", exc_info=True)
        task_manager.set_task_failed(task_id, str(e))

# Update the endpoint to use ADK pipeline
# In the process_youtube_url endpoint, replace:
# background_tasks.add_task(run_real_processing_pipeline, task_details["task_id"], request)

# With:
background_tasks.add_task(run_adk_processing_pipeline, task_details["task_id"], request)
```

### Phase 5: Testing and Migration of Existing Tests (1.5 days)

Comprehensive testing to ensure ADK implementation works correctly and migration of all existing tests to ADK patterns.

**Testing Strategy**:
1. First, create new ADK tests to verify the implementation
2. Then, migrate existing tests one by one
3. Run both old and new tests during migration
4. Remove old tests only after new ones pass

#### Unit Tests for ADK Components

**Create**: `/tests/test_adk_agents.py`

**Testing Best Practices**:
- Test each agent individually first
- Then test the full pipeline
- Mock external services (YouTube API, TTS)
- Test error cases
- Verify state updates

```python
"""
Unit tests for ADK agents and components.
"""
import pytest
import asyncio
import logging
from google.adk.sessions import Session, InMemorySessionService
from google.adk.runners import Runner, InMemoryRunner
from google.genai.types import Content, Part, UserContent

from src.agents.adk_agents import (
    transcript_agent,
    summarizer_agent,
    synthesizer_agent,
    podcast_pipeline
)

@pytest.mark.asyncio
async def test_transcript_agent():
    """Test the ADK transcript agent functionality."""
    logger = logging.getLogger(__name__)
    
    # This test demonstrates the ADK testing pattern:
    # 1. Create a runner with the agent
    # 2. Create a session with initial state
    # 3. Send a message to the agent
    # 4. Collect events as they stream
    # 5. Check the final state
    
    # Create runner and session
    runner = InMemoryRunner(agent=transcript_agent)
    session = await runner.session_service.create_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session",
        state={"video_ids": ["dQw4w9WgXcQ"]}  # Rick Roll for testing
    )
    
    # Create user message
    user_message = UserContent(
        parts=[Part(text="Fetch transcripts for the provided video IDs")]
    )
    
    # Run the transcript agent and collect events
    events = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=user_message
    ):
        events.append(event)
    
    # Get final session state
    final_session = await runner.session_service.get_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session"
    )
    
    # Verify results
    assert "transcripts" in final_session.state
    assert isinstance(final_session.state["transcripts"], dict)
    assert len(events) > 0
    logger.info("✅ Transcript agent test passed")

@pytest.mark.asyncio
async def test_summarizer_agent():
    """Test the ADK summarizer agent functionality."""
    logger = logging.getLogger(__name__)
    
    # Create runner and session with test transcript
    runner = InMemoryRunner(agent=summarizer_agent)
    session = await runner.session_service.create_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session",
        state={
            "transcripts": {
                "test_video": "This is a test transcript about machine learning and AI development..."
            }
        }
    )
    
    # Create user message
    user_message = UserContent(
        parts=[Part(text="Summarize the transcripts in the session state")]
    )
    
    # Run the summarizer agent
    events = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=user_message
    ):
        events.append(event)
    
    # Get final session state
    final_session = await runner.session_service.get_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session"
    )
    
    # Verify results
    assert "summaries" in final_session.state
    assert isinstance(final_session.state["summaries"], list)
    assert len(final_session.state["summaries"]) > 0
    logger.info("✅ Summarizer agent test passed")

@pytest.mark.asyncio
async def test_full_adk_pipeline():
    """Test the complete ADK pipeline end-to-end."""
    logger = logging.getLogger(__name__)
    
    # Create runner for the full pipeline
    runner = InMemoryRunner(agent=podcast_pipeline)
    session = await runner.session_service.create_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session",
        state={
            "video_ids": ["dQw4w9WgXcQ"],
            "output_dir": "./test_output"
        }
    )
    
    # Create user message
    user_message = UserContent(
        parts=[Part(text="Process YouTube video into podcast digest")]
    )
    
    # Run the complete pipeline
    events = []
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=user_message
    ):
        events.append(event)
        # Log progress
        if event.content and event.content.parts:
            logger.info(f"Pipeline event from {event.author}")
    
    # Get final session state
    final_session = await runner.session_service.get_session(
        app_name="test_app",
        user_id="test_user",
        session_id="test_session"
    )
    
    # Verify final results
    assert "final_audio_path" in final_session.state
    assert final_session.state["final_audio_path"] is not None
    assert "dialogue_script" in final_session.state
    assert len(final_session.state["dialogue_script"]) > 0
    
    logger.info("✅ Full ADK pipeline test passed")

@pytest.mark.asyncio
async def test_adk_pipeline_runner():
    """Test the ADK pipeline runner."""
    from src.runners.adk_pipeline import AdkPipelineRunner
    
    runner = AdkPipelineRunner()
    
    # Test with a simple video
    result = await runner.run_async(
        video_ids=["dQw4w9WgXcQ"],
        output_dir="./test_output"
    )
    
    # Verify results
    assert result["success"] is True
    assert result["final_audio_path"] is not None
    assert len(result["dialogue_script"]) > 0
    assert result["summary_count"] > 0
    
    logger.info("✅ ADK pipeline runner test passed")
```

#### Migration of Existing Tests

**Update ALL existing test files to use ADK patterns**:

1. **Agent Tests** - Update to use ADK event streaming:
   - `/tests/agents/test_audio_generator.py`
   - `/tests/agents/test_summarizer_agent.py`
   - `/tests/agents/test_synthesizer_agent.py`
   - `/tests/agents/test_transcript_fetcher.py`

2. **Pipeline Tests** - Migrate to ADK runner patterns:
   - `/tests/test_pipeline_runner.py`
   - `/tests/test_pipeline_integration.py`

3. **API Tests** - Update for ADK integration:
   - `/tests/api/test_api_v1.py`
   - `/tests/api/test_main_websocket_api.py`

**Example Test Migration Pattern**:
```python
# OLD: Direct agent testing (BEFORE)
def test_old_agent():
    # Old way - directly instantiate and call agent
    agent = SummarizerAgent()
    result = agent.run(transcript="test")
    assert result["summary"] != ""

# NEW: ADK event-based testing (AFTER)
@pytest.mark.asyncio
async def test_adk_agent():
    # New way - use runner and event streaming
    runner = InMemoryRunner(agent=summarizer_agent)
    
    # Create session with test data
    session = await runner.session_service.create_session(
        app_name="test", 
        user_id="test", 
        state={"transcript": "test transcript content"}
    )
    
    # Send message to agent
    events = []
    async for event in runner.run_async(
        user_id="test",
        session_id=session.id,
        new_message=UserContent(parts=[Part(text="Summarize the transcript")])
    ):
        events.append(event)
    
    # Get final state
    final_session = await runner.session_service.get_session(
        app_name="test",
        user_id="test", 
        session_id=session.id
    )
    
    # Check results
    assert len(events) > 0
    assert "summaries" in final_session.state
    assert len(final_session.state["summaries"]) > 0
```

**Key Differences**:
1. **Async**: Tests must be async with `@pytest.mark.asyncio`
2. **Runner**: Use InMemoryRunner instead of direct instantiation
3. **Session**: Create session with initial state
4. **Events**: Collect events instead of return values
5. **State**: Check final session state for results

#### Integration Tests

**Create**: `/tests/test_adk_integration.py`

```python
"""
Integration tests for ADK pipeline with API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_adk_pipeline_api_integration():
    """Test ADK pipeline integration with API endpoints."""
    
    # Submit a processing request
    response = client.post(
        "/api/v1/tasks/process_youtube_url",
        json={"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    
    assert response.status_code == 202
    task_data = response.json()
    assert "task_id" in task_data
    
    task_id = task_data["task_id"]
    
    # Check task status (may need to wait for completion in real test)
    status_response = client.get(f"/api/v1/status/{task_id}")
    assert status_response.status_code == 200
    
    status_data = status_response.json()
    assert status_data["task_id"] == task_id
    
    logger.info("✅ ADK API integration test passed")
```

## Migration Strategy

### Step 1: Parallel Implementation (1-2 days)

**Safe Migration Approach**:

- Keep existing custom agents running in production
- Implement ADK agents alongside existing system
- Use feature flags or separate endpoints for ADK testing
- Verify ADK implementation works correctly

### Step 2: Gradual Rollout (2-3 days)

- Test ADK implementation thoroughly with real data
- Switch individual endpoints one by one
- Monitor performance and functionality during transition
- Keep rollback capability available

### Step 3: Full Migration (1 day)

- Switch all endpoints to use ADK pipeline
- Remove custom agent implementations
- Update all imports and references
- Clean up unused custom code
- Migrate ALL tests to ADK patterns
- Run full test suite and fix failures
- Update documentation

## Learning Outcomes

By completing this migration, you will master:

### Agent Development Kit (ADK) Fundamentals (v1.0.0+ - April 2025 Release)
- ✅ **Agent/LlmAgent**: Create AI agents powered by language models
- ✅ **Workflow Agents**: Use SequentialAgent, ParallelAgent, LoopAgent for orchestration
- ✅ **FunctionTool**: Wrap Python functions as ADK-compatible tools
- ✅ **AgentTool**: Use agents as tools for hierarchical architectures
- ✅ **Session State**: Persistent state management across agent interactions
- ✅ **Event Streaming**: Process agent outputs as async event streams
- ✅ **Runner/InMemoryRunner**: Execute agents with proper context management
- ✅ **A2A Protocol**: Understand agent-to-agent communication standards

### ADK Patterns
- ✅ **Sequential Pipeline**: Chain agents for complex multi-step processing
- ✅ **Parallel Execution**: Concurrent processing for improved performance
- ✅ **Generator-Critic**: Iterative improvement and quality checking
- ✅ **Tool Integration**: Seamless integration of external services
- ✅ **State Management**: Efficient data flow between processing stages

### ADK Best Practices
- ✅ **Error Handling**: Robust error management in agent workflows
- ✅ **Resource Management**: Proper cleanup and resource handling
- ✅ **Testing Strategies**: Comprehensive testing with event streaming
- ✅ **Performance Optimization**: Efficient agent composition and execution
- ✅ **Code-First Development**: Define agent logic directly in Python
- ✅ **Safety Patterns**: Implement callbacks for guardrails and monitoring
- ✅ **Production Deployment**: Use Vertex AI Agent Engine for scaling

## Success Metrics

### Functional Requirements ✅
- [ ] All existing functionality preserved (YouTube → Transcript → Summary → Dialogue → Audio)
- [ ] API endpoints continue to work identically
- [ ] Performance same or better than current implementation
- [ ] Error handling maintains robustness

### Technical Requirements ✅
- [ ] All custom agents replaced with ADK LlmAgent
- [ ] ADK SequentialAgent used for pipeline orchestration
- [ ] FunctionTool wrappers created for existing tools
- [ ] ADK session state used for data flow
- [ ] AsyncRunner used for pipeline execution

### Learning Requirements ✅
- [ ] Understanding of core ADK agent types and patterns
- [ ] Practical experience with ADK session state management
- [ ] Knowledge of ADK tool integration patterns
- [ ] Experience with ADK testing strategies

## Risk Assessment

**Risk Level**: Medium

This is a significant architectural change but with good fallback options.

### Potential Issues
1. **ADK Learning Curve** - New patterns and concepts to master
2. **Dependency Management** - Additional ADK dependencies to manage
3. **Performance Impact** - Monitor for any performance changes
4. **Integration Complexity** - Ensure ADK works with existing infrastructure

### Mitigation Strategies
- Implement in parallel with existing system for safety
- Comprehensive testing before full migration
- Feature flags for easy rollback capability
- Performance monitoring and benchmarking
- Thorough documentation of ADK patterns used

## Implementation Timeline

| Phase | Duration | Key Deliverables | Success Criteria |
|-------|----------|------------------|------------------|
| Phase 1 | 1 day | ADK tool wrappers completed | Tools can be called from Python |
| Phase 2 | 2 days | All ADK agents implemented | Each agent works individually |
| Phase 3 | 1.5 days | ADK pipeline runner functional | Full pipeline processes a video |
| Phase 4 | 0.5 day | API integration updated | API endpoint triggers ADK pipeline |
| Phase 5 | 1.5 days | Testing migration complete | All tests passing |
| Migration | 2-3 days | Full production migration | Old code removed, ADK in production |
| **Total** | **8.5-9.5 days** | **Complete ADK system** | **System fully migrated to ADK** |

### Daily Checklist for Junior Engineers

**Day 1 (Phase 1)**:
- [ ] Create `adk_tools.py` file
- [ ] Test each tool function works
- [ ] Commit changes

**Day 2-3 (Phase 2)**:
- [ ] Create `adk_agents.py` file
- [ ] Test each agent individually
- [ ] Test pipeline agent
- [ ] Commit changes

**Day 4-5 (Phase 3)**:
- [ ] Create `adk_pipeline.py`
- [ ] Test runner with real video
- [ ] Verify audio output
- [ ] Commit changes

**Day 5 (Phase 4)**:
- [ ] Update API endpoints
- [ ] Test via API calls
- [ ] Commit changes

**Day 6-7 (Phase 5)**:
- [ ] Create new ADK tests
- [ ] Migrate existing tests
- [ ] Run full test suite
- [ ] Fix any failures
- [ ] Commit changes

## Files Modified Summary

### Created Files
- `src/tools/adk_tools.py` - Agent Development Kit tool wrappers (~150 lines)
- `src/agents/adk_agents.py` - ADK agent implementations (~200 lines)
- `src/runners/adk_pipeline.py` - ADK pipeline runner with event streaming (~250 lines)
- `tests/test_adk_agents.py` - ADK unit tests (~200 lines)
- `tests/test_adk_integration.py` - ADK integration tests (~100 lines)
- `.well-known/agent.json` - A2A protocol compliance file

### Modified Files
- `src/api/v1/endpoints/tasks.py` - API integration updates for ADK
- `requirements.txt` - Add google-adk dependency
- **ALL test files** - Migrated to ADK testing patterns:
  - `tests/agents/*.py` (4 files)
  - `tests/test_pipeline_*.py` (2 files)
  - `tests/api/*.py` (2+ files)

### Deprecated Files (after migration)
- `src/agents/base_agent.py` - Custom base agent class
- `src/agents/transcript_fetcher.py` - Custom transcript agent
- `src/agents/summarizer.py` - Custom summarizer agent  
- `src/agents/synthesizer.py` - Custom synthesizer agent
- `src/agents/audio_generator.py` - Custom audio agent
- `src/runners/simple_pipeline.py` - Custom pipeline runner

## Key Differences from Original Design

### Important ADK v1.0.0+ Changes

**For Junior Engineers - Key Points to Remember**:

1. **Event Streaming Pattern**: ADK uses async generators for event streaming, not simple return values
2. **Session Management**: Sessions must be created via `InMemorySessionService`, not instantiated directly
3. **Message Format**: Use `UserContent` with `Part` objects, not plain strings
4. **Runner Pattern**: Use `InMemoryRunner` for local development, `Runner` for production
5. **Tool Flexibility**: Simple Python functions work as tools; `FunctionTool` is optional
6. **Agent Naming**: `Agent` and `LlmAgent` are interchangeable in v1.0.0+
7. **State Updates**: State changes happen through session service, not direct modification

### New Patterns to Implement

1. **Event Processing**:
```python
async for event in runner.run_async(...):
    if event.is_final_response():
        # Process final output
    # Handle intermediate events
```

2. **A2A Protocol Compliance**:
```json
// .well-known/agent.json
{
  "name": "PodcastDigestAgent",
  "description": "Processes YouTube podcasts into audio digests",
  "version": "1.0.0"
}
```

3. **Safety Callbacks**:
```python
agent = Agent(
    name="SafeAgent",
    before_model_callback=safety_check,
    before_tool_callback=tool_validator
)
```

## Common Issues and Solutions

### Troubleshooting Guide for Junior Engineers

1. **Import Errors**
   ```python
   # Error: ImportError: cannot import name 'Agent' from 'google.adk.agents'
   # Solution: Check ADK is installed: pip install google-adk[all]
   ```

2. **Async/Await Issues**
   ```python
   # Error: RuntimeWarning: coroutine was never awaited
   # Solution: Make sure to use 'await' with async functions
   # Wrong: session = runner.session_service.create_session(...)
   # Right: session = await runner.session_service.create_session(...)
   ```

3. **State Not Updating**
   ```python
   # Issue: Agent can't see previous agent's output
   # Solution: Check output_key is set on agents
   # Check state keys match between agents
   ```

4. **No Events Streaming**
   ```python
   # Issue: No events coming from runner.run_async()
   # Solution: Make sure you're using 'async for', not regular 'for'
   # Check agent has work to do (state has required data)
   ```

5. **Tests Failing**
   ```python
   # Issue: Tests timeout
   # Solution: Mock external services (YouTube API, TTS)
   # Use smaller test data
   # Increase pytest timeout: @pytest.mark.timeout(30)
   ```

## Definition of Done

The ADK migration is complete when:

✅ All ADK tools implemented and tested  
✅ All ADK agents implemented with event streaming  
✅ ADK pipeline runner functional with session management  
✅ API integration updated with async event handling  
✅ All existing functionality preserved  
✅ Event streaming patterns implemented throughout  
✅ Session state management properly implemented  
✅ All existing tests migrated to ADK patterns
✅ New ADK-specific tests added
✅ Comprehensive test coverage with async testing  
✅ Performance benchmarking completed  
✅ A2A protocol compliance (agent.json file)  
✅ Documentation updated with ADK v1.0.0+ patterns  
✅ Migration successfully deployed to Vertex AI Agent Engine  
✅ Custom agent code removed and cleaned up

This migration will transform the project from a custom implementation to a proper Google Agent Development Kit (ADK) v1.0.0+ system, leveraging the same framework Google uses internally for Agentspace and Customer Engagement Suite. The migration includes comprehensive test updates to ensure all existing tests are converted to ADK patterns, providing excellent learning opportunities and a production-ready architecture using the April 2025 release of ADK.

## Final Tips for Junior Engineers

1. **Start Small**: Test each component individually before combining
2. **Use Logging**: Add lots of logger.info() statements to track flow
3. **Read Errors Carefully**: ADK provides good error messages
4. **Ask for Help**: Use the ADK Discord or team Slack
5. **Commit Often**: Make small commits as you progress
6. **Test Continuously**: Run tests after each change
7. **Document Issues**: Keep notes on problems and solutions

## Additional Resources

- 📺 **ADK YouTube Tutorials**: Search "Google Agent Development Kit tutorial"
- 📝 **ADK Blog Posts**: Check Google Developer Blog
- 💻 **Code Examples**: Study the ADK samples repository thoroughly
- 🤝 **Pair Programming**: Work with a senior engineer when stuck

Good luck with the migration! Remember: ADK makes agent development feel like regular software development. If you know Python, you can do this! 🚀