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
    vertexai=True,  # Use Vertex AI
    project="podcast-digest-agent",  # GCP project
    location="us-central1",  # GCP location
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
    vertexai=True,  # Use Vertex AI
    project="podcast-digest-agent",  # GCP project
    location="us-central1",  # GCP location
    description="Creates dialogue from transcripts",
    instruction="""
    You create podcast dialogue scripts from transcripts.

    1. Read transcripts from state['transcripts']
    2. If transcripts are available, create summaries and save to state['summaries']
    3. Generate a dialogue script in JSON format. ALWAYS start with:
       [
           {"speaker": "A", "line": "Welcome to today's podcast digest!"},
           {"speaker": "B", "line": "Today we're summarizing a YouTube video. Let's dive into the key points..."},
           ...
       ]
    4. Create an engaging, conversational dialogue between two speakers (A and B)
    5. Make sure to include the main topics and insights from the video
    6. Keep the tone friendly and informative
    7. Save the dialogue script to state['dialogue_script']

    If no transcripts are available, create a brief dialogue explaining the situation.
    """,
    output_key="dialogue_script",
)

# Step 3: Audio generator agent
audio_agent = LlmAgent(
    name="AudioGeneratorAgent",
    model="gemini-2.0-flash",
    vertexai=True,  # Use Vertex AI
    project="podcast-digest-agent",  # GCP project
    location="us-central1",  # GCP location
    description="Generates audio from dialogue",
    instruction="""
    You MUST generate audio files from dialogue scripts using the generate_audio_from_dialogue tool.

    CRITICAL STEPS - YOU MUST FOLLOW EXACTLY:
    1. Read dialogue_script from state['dialogue_script'] (this is a JSON array)
    2. Read output_dir from state['output_dir'] (e.g., "output_audio")
    3. Convert the dialogue_script to a JSON string if it's not already
    4. CALL the generate_audio_from_dialogue tool with these parameters:
       - output_dir: exact value from state['output_dir']
       - dialogue_script: the JSON string of the dialogue
    5. The tool will return a file path string (e.g., "/path/to/audio.mp3")
    6. Save the returned path directly to state['final_audio_path']

    DO NOT RETURN JSON. DO NOT GUESS THE PATH. YOU MUST CALL THE TOOL.

    Example:
    - Input: state['dialogue_script'] = [{"speaker": "A", "line": "Hello"}]
    - Input: state['output_dir'] = "output_audio"
    - Action: Call generate_audio_from_dialogue(output_dir="output_audio", dialogue_script=...)
    - Tool returns: "/path/to/output_audio/podcast_digest_20250526_164530.mp3"
    - Save to state: state['final_audio_path'] = "/path/to/audio.mp3"
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
