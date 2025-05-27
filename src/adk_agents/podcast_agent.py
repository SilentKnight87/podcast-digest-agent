"""
Main ADK agent for podcast digest generation.
"""
import logging

from google.adk.agents import LlmAgent

from ..adk_tools.audio_tools import generate_audio_from_dialogue

# Import our ADK-compatible tools
from ..adk_tools.transcript_tools import process_multiple_transcripts

logger = logging.getLogger(__name__)

# Main podcast digest agent
podcast_digest_agent = LlmAgent(
    name="PodcastDigestAgent",
    model="gemini-2.0-flash",
    description="Agent that processes YouTube videos to create podcast digests",
    instruction="""
    You are the main podcast digest agent. When given YouTube video IDs, you must:

    1. First, use the process_multiple_transcripts tool to fetch transcripts for the video IDs
    2. After receiving transcripts, create comprehensive summaries of the key content
    3. Generate a conversational dialogue script between two speakers (A and B) from summaries
    4. Finally, use generate_audio_from_dialogue to create the final audio file

    IMPORTANT:
    - The video IDs are provided in state['video_ids']
    - The output directory is provided in state['output_dir']
    - When calling generate_audio_from_dialogue, use the output_dir from state

    CRITICAL: If transcript fetching fails for a video:
    - DO NOT retry the same video
    - Create a brief dialogue explaining that the video transcript was unavailable
    - Continue with the audio generation using this fallback dialogue

    The dialogue script must be a JSON array string with this format:
    [
        {"speaker": "A", "line": "Welcome to today's podcast digest!"},
        {"speaker": "B", "line": "Today we're covering some fascinating content..."},
        {"speaker": "A", "line": "That's right! Let's dive into the key points..."}
    ]

    Make the dialogue engaging, informative, and natural-sounding. Include:
    - A welcoming introduction
    - Discussion of the main topics (or explanation if transcripts unavailable)
    - Key insights and takeaways (if available)
    - A proper conclusion

    After generating audio, YOU MUST save the results to state using the exact keys:
    - state['transcripts'] = the transcript data (or error info if failed)
    - state['summaries'] = the summaries you created (or empty list if no transcripts)
    - state['dialogue_script'] = the dialogue array
    - state['final_audio_path'] = the audio file path from the tool response

    ALWAYS complete the full pipeline even if transcripts fail. Generate audio with any content.
    """,
    tools=[process_multiple_transcripts, generate_audio_from_dialogue],
    # Specify outputs that should be saved to state
    output_key="final_result",
)

# Export the main agent
root_agent = podcast_digest_agent
