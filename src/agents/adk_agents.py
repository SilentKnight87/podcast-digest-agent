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

# Advanced ADK Patterns (commented out to avoid agent parent conflicts)
# These are examples of advanced patterns you can use with ADK

# # Parallel processing for multiple videos
# from google.adk.agents import ParallelAgent

# # Note: We need to create new instances of agents for different pipelines
# # because an agent can only have one parent
# parallel_transcript_agent = ParallelAgent(
#     name="ParallelTranscriptFetcher",
#     description="Process multiple videos simultaneously",
#     sub_agents=[
#         Agent(
#             name="TranscriptFetcherParallel",
#             model="gemini-2.0-flash",
#             description="Fetches YouTube video transcripts for parallel processing",
#             instruction=transcript_agent.instruction,
#             tools=[transcript_tool],
#             output_key="transcripts"
#         )
#     ]
# )

# # Hierarchical Agent Pattern (Agent as Tool)
# from google.adk.tools import agent_tool as adk_agent_tool

# # Wrap agents as tools for use by other agents
# # Note: These create agent wrappers, different from our imported transcript_tool
# transcript_agent_tool = adk_agent_tool.AgentTool(agent=transcript_agent)
# summarizer_agent_tool = adk_agent_tool.AgentTool(agent=summarizer_agent)

# # Iterative improvement pattern
# from google.adk.agents import LoopAgent

# quality_checker_agent = Agent(
#     name="QualityChecker",
#     model="gemini-2.0-flash",
#     description="Evaluates summary quality and suggests improvements",
#     instruction="""
#     Evaluate the summary quality from session state key 'summaries'.
#     Rate the quality as 'excellent', 'good', or 'needs_improvement'.
#     If 'needs_improvement', provide specific suggestions.
#     Save your assessment to session state key 'quality_assessment'.
#     """,
#     output_key="quality_assessment"
# )

# iterative_summary_pipeline = LoopAgent(
#     name="IterativeSummaryRefiner",
#     description="Iteratively improve summary quality",
#     max_iterations=3,
#     sub_agents=[
#         summarizer_agent,
#         quality_checker_agent
#     ]
# )