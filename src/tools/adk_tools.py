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