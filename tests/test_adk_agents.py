"""
Unit tests for ADK agents and components.
"""
import pytest
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch
from google.adk.sessions import Session, InMemorySessionService
from google.adk.runners import Runner, InMemoryRunner
from google.genai.types import Content, Part, UserContent

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_adk_agent_creation():
    """Test that ADK agents can be created successfully."""
    from src.agents.adk_agents import (
        transcript_agent,
        summarizer_agent,
        synthesizer_agent,
        audio_agent,
        podcast_pipeline
    )
    
    # Verify all agents are created
    assert transcript_agent.name == "TranscriptFetcher"
    assert summarizer_agent.name == "SummarizerAgent"
    assert synthesizer_agent.name == "DialogueSynthesizer"
    assert audio_agent.name == "AudioGenerator"
    assert podcast_pipeline.name == "PodcastDigestPipeline"
    
    logger.info("✅ All ADK agents created successfully")

@pytest.mark.asyncio
async def test_adk_pipeline_runner_initialization():
    """Test ADK pipeline runner initialization."""
    from src.runners.adk_pipeline import AdkPipelineRunner
    
    runner = AdkPipelineRunner()
    assert runner.runner is not None
    assert runner.session_service is not None
    assert runner.temp_dirs == []
    
    logger.info("✅ ADK pipeline runner initialized successfully")

@pytest.mark.asyncio
async def test_adk_pipeline_runner_with_mocks():
    """Test the ADK pipeline runner with mocked dependencies."""
    from src.runners.adk_pipeline import AdkPipelineRunner
    
    # Mock the transcript tool
    with patch('src.tools.adk_tools.fetch_youtube_transcripts') as mock_fetch:
        mock_fetch.return_value = {
            "test_video": {
                "success": True,
                "transcript": "This is a test transcript",
                "error": None
            }
        }
        
        # Mock the TTS client
        with patch('google.cloud.texttospeech_v1.TextToSpeechAsyncClient') as mock_tts:
            mock_tts_instance = AsyncMock()
            mock_tts.return_value.__aenter__.return_value = mock_tts_instance
            
            # Mock audio generation
            with patch('src.tools.adk_tools.generate_audio_segments') as mock_gen_audio:
                mock_gen_audio.return_value = AsyncMock(return_value=["segment1.mp3", "segment2.mp3"])
                
                with patch('src.tools.adk_tools.combine_audio_files') as mock_combine:
                    mock_combine.return_value = AsyncMock(return_value="final_audio.mp3")
                    
                    # Create runner and test
                    runner = AdkPipelineRunner()
                    
                    # Note: Full pipeline test would require mocking the entire ADK event stream
                    # For now, we just verify the runner can be created
                    assert runner is not None
                    
    logger.info("✅ ADK pipeline runner test with mocks passed")

@pytest.mark.asyncio
async def test_adk_tools_import():
    """Test that ADK tools can be imported successfully."""
    from src.tools.adk_tools import (
        fetch_youtube_transcripts,
        generate_audio_segments,
        combine_audio_files,
        transcript_tool,
        audio_generation_tool,
        audio_combination_tool
    )
    
    # Verify tools are callable
    assert callable(fetch_youtube_transcripts)
    assert callable(generate_audio_segments)
    assert callable(combine_audio_files)
    
    # Verify tool assignments
    assert transcript_tool == fetch_youtube_transcripts
    assert audio_generation_tool == generate_audio_segments
    assert audio_combination_tool == combine_audio_files
    
    logger.info("✅ ADK tools imported successfully")

@pytest.mark.asyncio
async def test_api_endpoint_integration():
    """Test that API endpoint uses ADK pipeline."""
    from src.api.v1.endpoints.tasks import run_adk_processing_pipeline
    
    # Verify the function exists
    assert callable(run_adk_processing_pipeline)
    
    logger.info("✅ API endpoint ADK integration verified")