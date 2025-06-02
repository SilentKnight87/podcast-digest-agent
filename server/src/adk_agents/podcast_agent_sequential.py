"""
Sequential ADK agent for podcast digest generation.
"""

import logging

from google.adk.agents import LlmAgent, SequentialAgent

from ..adk_tools.audio_tools import generate_audio_from_dialogue

# Import our ADK-compatible tools
from ..adk_tools.transcript_tools import process_multiple_transcripts

logger = logging.getLogger(__name__)

# Step 1: Transcript fetcher agent
transcript_agent = LlmAgent(
    name="TranscriptFetcherAgent",
    model="gemini-2.0-flash",
    description="Fetches YouTube video transcripts",
    instruction="""
    You fetch YouTube video transcripts.

    1. Look for video IDs in state['video_ids']
    2. Use process_multiple_transcripts tool to fetch the transcripts
    3. Save the results to state['transcripts']

    If fetching fails, save error information to state['transcripts'].
    """,
    tools=[process_multiple_transcripts],
    output_key="transcripts",
)

# Step 2: Summarizer and dialogue creator agent
dialogue_agent = LlmAgent(
    name="DialogueCreatorAgent",
    model="gemini-2.0-flash",
    description="Creates dialogue from transcripts",
    instruction="""
    You create podcast dialogue scripts from transcripts.

    1. Read transcripts from state['transcripts']. This will be a dictionary with:
       - 'results': dict mapping video_id to transcript data
       - 'total_videos': number of videos
       - 'successful_count': number of successful transcripts
    
    2. Extract the actual transcript text from the results:
       - Look in state['transcripts']['results'] for each video_id
       - Each video result has 'success', 'transcript', and possibly 'error' fields
       - If 'success' is True, use the 'transcript' field content
    
    3. Analyze the transcript content and create a dialogue about the ACTUAL video topics.

    CRITICAL: Your ENTIRE output must be ONLY a valid JSON array string. Nothing else.
    
    Output format - your complete response should look EXACTLY like this:
    [{"speaker": "A", "line": "Welcome to today's podcast digest!"}, {"speaker": "B", "line": "Today we're discussing [ACTUAL TOPIC FROM VIDEO]..."}, {"speaker": "A", "line": "[Specific point from transcript]"}, {"speaker": "B", "line": "[Another specific detail from video]"}]
    
    Rules:
    - NO text before or after the JSON
    - NO markdown code blocks
    - NO explanations
    - ONLY the raw JSON array
    - Must discuss ACTUAL content from the transcript
    - 8-12 dialogue exchanges
    - Alternate speakers A and B

    If no transcript available, output ONLY:
    [{"speaker": "A", "line": "Welcome to today's podcast digest!"}, {"speaker": "B", "line": "Unfortunately, we couldn't retrieve the transcript for this video. This might happen if the video has no captions or if there was a technical issue."}]
    """,
    output_key="dialogue_script",
)

# Step 3: Audio generator agent
audio_agent = LlmAgent(
    name="AudioGeneratorAgent",
    model="gemini-2.0-flash",
    description="Generates audio from dialogue",
    instruction="""
    You generate audio files from dialogue scripts using the generate_audio_from_dialogue tool.

    Steps:
    1. Read dialogue_script from state['dialogue_script'] (this is a JSON string)
    2. Read output_dir from state['output_dir'] (e.g., "/tmp")
    3. Call generate_audio_from_dialogue with these exact parameters:
       - output_dir: value from state['output_dir']
       - dialogue_script: value from state['dialogue_script']
    4. The tool returns a file path string (e.g., "/tmp/podcast_digest_20250602_123456.mp3")
    5. Output ONLY this file path. Nothing else.

    Example:
    If the tool returns: /tmp/podcast_digest_20250602_123456.mp3
    You output ONLY: /tmp/podcast_digest_20250602_123456.mp3
    
    DO NOT add any text like "The audio was generated at..." or "File saved to..."
    ONLY output the path.
    """,
    tools=[generate_audio_from_dialogue],
    output_key="final_audio_path",
)

# Main sequential agent
podcast_digest_agent = SequentialAgent(
    name="PodcastDigestSequentialAgent",
    description="Sequential agent that processes YouTube videos to create podcast digests",
    sub_agents=[transcript_agent, dialogue_agent, audio_agent],
)

# Export the main agent
root_agent = podcast_digest_agent
