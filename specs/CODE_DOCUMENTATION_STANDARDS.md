# CODE_DOCUMENTATION_STANDARDS.md

## Overview
This document establishes comprehensive code documentation standards for the Podcast Digest Agent project, ensuring consistent, high-quality documentation across all codebases (Python backend, TypeScript frontend). These standards follow Google ADK best practices and industry conventions.

## Table of Contents
1. [General Principles](#general-principles)
2. [Python Documentation Standards](#python-documentation-standards)
3. [TypeScript/JavaScript Documentation Standards](#typescriptjavascript-documentation-standards)
4. [API Documentation](#api-documentation)
5. [ADK Agent Documentation](#adk-agent-documentation)
6. [Code Comments Guidelines](#code-comments-guidelines)
7. [Documentation Tools and Automation](#documentation-tools-and-automation)
8. [Examples and Templates](#examples-and-templates)

## General Principles

### Core Philosophy
- **Self-Documenting Code First**: Write clear, readable code that minimizes the need for comments
- **Document the Why, Not the What**: Focus on intent, business logic, and non-obvious decisions
- **Keep Documentation Close to Code**: Documentation should live with the code it describes
- **Maintain Documentation**: Treat documentation as part of the code that must be updated together

### Documentation Hierarchy
1. **Code Structure**: Clear naming, proper organization
2. **Type Annotations**: Full type hints/interfaces
3. **Docstrings/JSDoc**: Function and class documentation
4. **Inline Comments**: Complex logic explanation
5. **External Documentation**: Architecture, guides, README files

## Python Documentation Standards

### Module-Level Documentation
```python
"""Module for handling YouTube transcript fetching and processing.

This module provides functionality to fetch transcripts from YouTube videos
using the YouTube Transcript API and process them for use in the podcast
digest pipeline. It handles various edge cases including missing transcripts,
multiple language support, and rate limiting.

Example:
    Basic usage of the transcript fetcher::

        from src.agents.transcript_fetcher import TranscriptFetcher

        agent = TranscriptFetcher()
        transcript = await agent.fetch_transcript("https://youtube.com/watch?v=...")

Note:
    This module requires a valid YouTube API key configured in the environment.

Attributes:
    DEFAULT_LANGUAGES (List[str]): Preferred languages for transcript fetching
    MAX_RETRIES (int): Maximum number of retry attempts for failed requests
"""

from typing import List, Optional, Dict, Any
import logging

# Module-level constants should be documented
DEFAULT_LANGUAGES: List[str] = ["en", "en-US", "en-GB"]  # Preferred transcript languages
MAX_RETRIES: int = 3  # Maximum retry attempts for API calls
```

### Class Documentation
```python
class TranscriptFetcherAgent(BaseAgent):
    """Agent responsible for fetching and processing YouTube video transcripts.

    This agent extends BaseAgent to provide specialized functionality for
    retrieving transcripts from YouTube videos. It implements retry logic,
    language fallback, and error handling specific to the YouTube API.

    The agent follows the ADK pattern for asynchronous execution and integrates
    with the broader podcast digest pipeline through standardized interfaces.

    Attributes:
        youtube_client: Client for interacting with YouTube API
        language_preferences: Ordered list of preferred transcript languages
        retry_config: Configuration for retry behavior

    Example:
        Creating and using the transcript fetcher::

            agent = TranscriptFetcherAgent(
                name="transcript_fetcher",
                language_preferences=["en", "es"],
                retry_config={"max_attempts": 3, "backoff": 2.0}
            )

            result = await agent.process_video("https://youtube.com/watch?v=...")

    Note:
        This agent requires the following environment variables:
        - YOUTUBE_API_KEY: Valid YouTube Data API v3 key
        - TRANSCRIPT_CACHE_DIR: Optional cache directory for transcripts

    See Also:
        :class:`BaseAgent`: Parent class defining core agent interface
        :mod:`src.tools.transcript_tools`: Utility functions for transcript processing
    """

    def __init__(
        self,
        name: str = "transcript_fetcher",
        model: str = "gemini-2.0-flash",
        language_preferences: Optional[List[str]] = None,
        retry_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the transcript fetcher agent.

        Args:
            name: Unique identifier for this agent instance
            model: LLM model to use for transcript processing
            language_preferences: Ordered list of preferred languages.
                Defaults to English variants if not specified.
            retry_config: Configuration for retry behavior containing:
                - max_attempts (int): Maximum retry attempts (default: 3)
                - backoff (float): Exponential backoff multiplier (default: 2.0)
                - max_delay (float): Maximum delay between retries (default: 60.0)
            **kwargs: Additional arguments passed to parent BaseAgent

        Raises:
            ValueError: If language_preferences contains invalid language codes
            ConfigurationError: If required environment variables are missing
        """
        super().__init__(name=name, model=model, **kwargs)
        self.language_preferences = language_preferences or DEFAULT_LANGUAGES
        self.retry_config = retry_config or self._default_retry_config()
```

### Method Documentation
```python
async def fetch_transcript(
    self,
    video_url: str,
    language: Optional[str] = None,
    include_timestamps: bool = True
) -> TranscriptResult:
    """Fetch transcript for a YouTube video with automatic language fallback.

    Attempts to retrieve the transcript in the requested language, falling back
    to other available languages if necessary. Implements exponential backoff
    for rate limiting and transient errors.

    Args:
        video_url: Full YouTube video URL or video ID
        language: ISO 639-1 language code (e.g., 'en', 'es'). If None,
            uses the first available language from language_preferences
        include_timestamps: Whether to include timestamp information in
            the returned transcript segments

    Returns:
        TranscriptResult containing:
            - text (str): Full transcript text
            - segments (List[TranscriptSegment]): Individual transcript segments
            - language (str): Actual language of retrieved transcript
            - duration (float): Total video duration in seconds

    Raises:
        TranscriptNotFoundError: No transcript available in any language
        VideoNotFoundError: Invalid video URL or video not accessible
        APIQuotaExceededError: YouTube API quota exceeded
        NetworkError: Connection issues preventing API access

    Example:
        Fetching a transcript with fallback::

            try:
                result = await agent.fetch_transcript(
                    "https://youtube.com/watch?v=dQw4w9WgXcQ",
                    language="en",
                    include_timestamps=True
                )
                print(f"Transcript in {result.language}: {result.text[:100]}...")
            except TranscriptNotFoundError:
                print("No transcript available for this video")

    Note:
        The method implements smart caching to avoid repeated API calls for
        the same video within a 24-hour period.
    """
    # Implementation details...
```

### Property Documentation
```python
@property
def is_configured(self) -> bool:
    """Check if the agent is properly configured for operation.

    Verifies that all required environment variables and dependencies
    are available for the agent to function correctly.

    Returns:
        True if all requirements are met, False otherwise

    Note:
        This property is checked before agent execution in the pipeline.
    """
    return bool(os.getenv("YOUTUBE_API_KEY")) and self.youtube_client is not None

@cached_property
def supported_languages(self) -> List[str]:
    """Retrieve list of languages supported by the YouTube API.

    This property is cached after the first access to avoid repeated
    API calls. The cache is valid for the lifetime of the agent instance.

    Returns:
        List of ISO 639-1 language codes supported by YouTube

    Example:
        Checking supported languages::

            if "fr" in agent.supported_languages:
                transcript = await agent.fetch_transcript(url, language="fr")
    """
    return self._fetch_supported_languages()
```

### Exception Documentation
```python
class TranscriptNotFoundError(Exception):
    """Raised when no transcript is available for the requested video.

    This exception indicates that YouTube does not have any transcript
    (auto-generated or manual) available for the video in any language.

    Attributes:
        video_id (str): The YouTube video ID that was requested
        attempted_languages (List[str]): Languages that were checked
        message (str): Human-readable error description

    Example:
        Handling missing transcripts::

            try:
                transcript = await fetcher.fetch_transcript(video_url)
            except TranscriptNotFoundError as e:
                logger.warning(f"No transcript for video {e.video_id}")
                # Fallback to audio transcription
                transcript = await audio_transcriber.process(video_url)
    """

    def __init__(self, video_id: str, attempted_languages: List[str]):
        self.video_id = video_id
        self.attempted_languages = attempted_languages
        self.message = (
            f"No transcript found for video {video_id}. "
            f"Attempted languages: {', '.join(attempted_languages)}"
        )
        super().__init__(self.message)
```

### Type Aliases and Constants
```python
from typing import TypeAlias, Literal, TypedDict

# Document type aliases with clear descriptions
TranscriptLanguage: TypeAlias = Literal["en", "es", "fr", "de", "ja", "ko", "pt", "ru"]
"""Supported transcript languages using ISO 639-1 codes."""

class TranscriptSegment(TypedDict):
    """Individual segment of a video transcript.

    Attributes:
        text: The transcript text for this segment
        start: Start time in seconds
        duration: Duration of this segment in seconds
        confidence: Optional confidence score (0-1) for auto-generated transcripts
    """
    text: str
    start: float
    duration: float
    confidence: Optional[float]

# Document constants with their purpose and constraints
MAX_TRANSCRIPT_LENGTH: int = 50_000
"""Maximum allowed transcript length in characters to prevent memory issues."""

CACHE_TTL_SECONDS: int = 86_400  # 24 hours
"""Time-to-live for cached transcripts in seconds."""
```

## TypeScript/JavaScript Documentation Standards

### Module Documentation
```typescript
/**
 * @fileoverview Audio processing and waveform generation utilities.
 *
 * This module provides React components and utilities for audio playback,
 * waveform visualization, and real-time audio processing in the podcast
 * digest interface. It leverages the Web Audio API for efficient audio
 * manipulation and Canvas API for visualization.
 *
 * @module components/audio
 * @requires react
 * @requires @/lib/audio-utils
 *
 * @example
 * ```tsx
 * import { WaveformPlayer, AudioProcessor } from '@/components/audio';
 *
 * function AudioPlayer() {
 *   return <WaveformPlayer src="/audio/podcast.mp3" />;
 * }
 * ```
 */

// Module-level constants with JSDoc
/**
 * Default sample rate for audio processing in Hz.
 * @constant {number}
 */
export const DEFAULT_SAMPLE_RATE = 44100;

/**
 * Maximum number of waveform points to render for performance.
 * @constant {number}
 */
export const MAX_WAVEFORM_POINTS = 1000;
```

### Interface and Type Documentation
```typescript
/**
 * Configuration options for the audio processing pipeline.
 *
 * @interface ProcessingConfig
 * @property {number} sampleRate - Audio sample rate in Hz (default: 44100)
 * @property {number} bufferSize - Processing buffer size in samples
 * @property {boolean} enableNormalization - Whether to normalize audio levels
 * @property {NoiseReductionLevel} noiseReduction - Level of noise reduction to apply
 *
 * @example
 * ```typescript
 * const config: ProcessingConfig = {
 *   sampleRate: 48000,
 *   bufferSize: 2048,
 *   enableNormalization: true,
 *   noiseReduction: 'medium'
 * };
 * ```
 */
export interface ProcessingConfig {
  sampleRate?: number;
  bufferSize?: number;
  enableNormalization?: boolean;
  noiseReduction?: NoiseReductionLevel;
}

/**
 * Noise reduction intensity levels.
 * - 'off': No noise reduction applied
 * - 'low': Minimal noise reduction, preserves most detail
 * - 'medium': Balanced noise reduction
 * - 'high': Aggressive noise reduction, may affect quality
 *
 * @typedef {'off' | 'low' | 'medium' | 'high'} NoiseReductionLevel
 */
export type NoiseReductionLevel = 'off' | 'low' | 'medium' | 'high';

/**
 * Result of audio analysis operation.
 *
 * @interface AnalysisResult
 * @template T - Type of the analysis data
 *
 * @property {boolean} success - Whether analysis completed successfully
 * @property {T} [data] - Analysis results if successful
 * @property {Error} [error] - Error details if analysis failed
 * @property {AnalysisMetadata} metadata - Additional analysis information
 */
export interface AnalysisResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: Error;
  metadata: AnalysisMetadata;
}
```

### React Component Documentation
```typescript
/**
 * Interactive waveform visualization component with playback controls.
 *
 * Renders an audio waveform using Canvas API and provides interactive
 * playback controls including play/pause, seek, and volume adjustment.
 * The component automatically handles loading states and error conditions.
 *
 * @component
 * @example
 * ```tsx
 * // Basic usage
 * <WaveformPlayer src="/audio/episode.mp3" />
 *
 * // With all props
 * <WaveformPlayer
 *   src="/audio/episode.mp3"
 *   height={200}
 *   waveColor="#3b82f6"
 *   progressColor="#1d4ed8"
 *   onPlay={() => console.log('Started playing')}
 *   onError={(error) => console.error('Playback error:', error)}
 * />
 * ```
 *
 * @param {WaveformPlayerProps} props - Component properties
 * @returns {JSX.Element} Rendered waveform player
 *
 * @since 1.0.0
 * @see {@link useAudioContext} for audio context management
 * @see {@link AudioProcessor} for processing pipeline
 */
export const WaveformPlayer: React.FC<WaveformPlayerProps> = ({
  src,
  height = 128,
  waveColor = '#3b82f6',
  progressColor = '#1d4ed8',
  backgroundColor = 'transparent',
  onPlay,
  onPause,
  onSeek,
  onError,
  className,
  ...rest
}) => {
  // Component implementation
};

/**
 * Props for the WaveformPlayer component.
 *
 * @interface WaveformPlayerProps
 * @extends {React.HTMLAttributes<HTMLDivElement>}
 *
 * @property {string} src - URL or path to the audio file
 * @property {number} [height=128] - Height of the waveform canvas in pixels
 * @property {string} [waveColor='#3b82f6'] - Color of the waveform
 * @property {string} [progressColor='#1d4ed8'] - Color of the progress indicator
 * @property {string} [backgroundColor='transparent'] - Canvas background color
 * @property {() => void} [onPlay] - Callback fired when playback starts
 * @property {() => void} [onPause] - Callback fired when playback pauses
 * @property {(time: number) => void} [onSeek] - Callback fired on seek with time in seconds
 * @property {(error: Error) => void} [onError] - Callback fired on playback error
 */
export interface WaveformPlayerProps extends React.HTMLAttributes<HTMLDivElement> {
  src: string;
  height?: number;
  waveColor?: string;
  progressColor?: string;
  backgroundColor?: string;
  onPlay?: () => void;
  onPause?: () => void;
  onSeek?: (time: number) => void;
  onError?: (error: Error) => void;
}
```

### Hook Documentation
```typescript
/**
 * Custom hook for managing audio context and playback state.
 *
 * Provides a centralized way to manage Web Audio API context across
 * components, handling browser autoplay policies and context suspension.
 * The hook automatically resumes context on user interaction.
 *
 * @hook
 * @param {AudioContextOptions} [options] - Optional Web Audio API context options
 * @returns {UseAudioContextReturn} Audio context and control methods
 *
 * @example
 * ```tsx
 * function AudioComponent() {
 *   const { context, isReady, resume, suspend } = useAudioContext();
 *
 *   useEffect(() => {
 *     if (isReady) {
 *       // Initialize audio nodes
 *       const oscillator = context.createOscillator();
 *       // ...
 *     }
 *   }, [isReady, context]);
 *
 *   return (
 *     <button onClick={resume}>
 *       Start Audio Context
 *     </button>
 *   );
 * }
 * ```
 *
 * @throws {Error} Throws if Web Audio API is not supported
 *
 * @since 1.0.0
 * @see [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
 */
export function useAudioContext(options?: AudioContextOptions): UseAudioContextReturn {
  const [context, setContext] = useState<AudioContext | null>(null);
  const [isReady, setIsReady] = useState(false);

  // Implementation details...
}

/**
 * Return type for useAudioContext hook.
 *
 * @interface UseAudioContextReturn
 * @property {AudioContext | null} context - The Web Audio API context instance
 * @property {boolean} isReady - Whether context is created and running
 * @property {() => Promise<void>} resume - Resume suspended audio context
 * @property {() => Promise<void>} suspend - Suspend active audio context
 * @property {AudioContextState} state - Current context state
 */
export interface UseAudioContextReturn {
  context: AudioContext | null;
  isReady: boolean;
  resume: () => Promise<void>;
  suspend: () => Promise<void>;
  state: AudioContextState;
}
```

### Utility Function Documentation
```typescript
/**
 * Analyzes audio buffer to extract waveform data for visualization.
 *
 * Processes raw audio samples to generate normalized waveform points
 * suitable for rendering. Implements downsampling for performance and
 * peak detection for accurate visualization.
 *
 * @function
 * @param {AudioBuffer} buffer - Web Audio API AudioBuffer to analyze
 * @param {number} [targetPoints=1000] - Desired number of waveform points
 * @param {WaveformOptions} [options={}] - Additional processing options
 * @returns {Float32Array} Normalized waveform data points (-1 to 1)
 *
 * @example
 * ```typescript
 * // Basic usage
 * const waveform = extractWaveform(audioBuffer);
 *
 * // With options
 * const detailedWaveform = extractWaveform(audioBuffer, 2000, {
 *   normalize: true,
 *   logarithmic: true,
 *   smoothing: 0.8
 * });
 * ```
 *
 * @throws {TypeError} If buffer is not a valid AudioBuffer
 * @throws {RangeError} If targetPoints is less than 2
 *
 * @since 1.0.0
 * @complexity O(n) where n is the number of samples
 */
export function extractWaveform(
  buffer: AudioBuffer,
  targetPoints: number = 1000,
  options: WaveformOptions = {}
): Float32Array {
  if (!(buffer instanceof AudioBuffer)) {
    throw new TypeError('First argument must be an AudioBuffer');
  }

  if (targetPoints < 2) {
    throw new RangeError('targetPoints must be at least 2');
  }

  const {
    normalize = true,
    logarithmic = false,
    smoothing = 0
  } = options;

  // Implementation...
}
```

## API Documentation

### FastAPI Endpoint Documentation
```python
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["processing"])

@router.post(
    "/process",
    response_model=ProcessingResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start podcast processing",
    description="""
    Initiates asynchronous processing of a podcast from a YouTube URL.

    The processing pipeline includes:
    1. Transcript fetching
    2. Content summarization
    3. Script synthesis
    4. Audio generation

    Returns a task ID that can be used to track progress via WebSocket
    or polling the status endpoint.
    """,
    responses={
        202: {
            "description": "Processing started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "task_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "pending",
                        "message": "Processing started"
                    }
                }
            }
        },
        400: {
            "description": "Invalid request parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Invalid YouTube URL format"
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Rate limit exceeded. Please try again in 3600 seconds."
                    }
                }
            }
        }
    },
    tags=["processing"]
)
async def start_processing(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> ProcessingResponse:
    """
    Start processing a podcast from a YouTube URL.

    Args:
        request: Processing request containing YouTube URL and options
        background_tasks: FastAPI background task manager
        current_user: Authenticated user making the request

    Returns:
        ProcessingResponse with task ID and initial status

    Raises:
        HTTPException: 400 if URL is invalid, 429 if rate limited

    Note:
        Processing is performed asynchronously. Use the returned task_id
        to track progress via WebSocket connection or status endpoint.
    """
    # Validate URL format
    if not is_valid_youtube_url(request.youtube_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL format"
        )

    # Check rate limits
    if not await check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again in 3600 seconds."
        )

    # Create task and start processing
    task_id = str(uuid.uuid4())
    background_tasks.add_task(
        process_podcast,
        task_id=task_id,
        url=request.youtube_url,
        options=request.options,
        user_id=current_user.id
    )

    return ProcessingResponse(
        task_id=task_id,
        status="pending",
        message="Processing started"
    )
```

### Pydantic Model Documentation
```python
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List, Literal
from datetime import datetime

class ProcessingRequest(BaseModel):
    """Request model for initiating podcast processing.

    Attributes:
        youtube_url: Valid YouTube video URL to process
        options: Optional processing configuration

    Example:
        ```json
        {
            "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "options": {
                "target_duration": 600,
                "summary_style": "conversational",
                "voice_config": {
                    "primary": "en-US-Neural2-C",
                    "secondary": "en-US-Neural2-J"
                }
            }
        }
        ```
    """

    youtube_url: HttpUrl = Field(
        ...,
        description="YouTube video URL to process",
        example="https://youtube.com/watch?v=dQw4w9WgXcQ"
    )

    options: Optional[ProcessingOptions] = Field(
        None,
        description="Optional processing configuration"
    )

    @validator('youtube_url')
    def validate_youtube_url(cls, v):
        """Ensure URL is from youtube.com or youtu.be."""
        allowed_hosts = ['youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com']
        if v.host not in allowed_hosts:
            raise ValueError(f"URL must be from YouTube, got {v.host}")
        return v

    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                "options": {
                    "target_duration": 600,
                    "summary_style": "bullet_points"
                }
            }
        }

class ProcessingOptions(BaseModel):
    """Configuration options for podcast processing.

    All fields are optional and will use defaults if not specified.

    Attributes:
        target_duration: Target duration for output audio in seconds (300-1800)
        summary_style: Style of summary generation
        voice_config: Text-to-speech voice configuration
        quality: Output audio quality preset
    """

    target_duration: Optional[int] = Field(
        600,
        ge=300,
        le=1800,
        description="Target duration for output audio in seconds"
    )

    summary_style: Optional[Literal["conversational", "bullet_points", "narrative"]] = Field(
        "conversational",
        description="Style of summary generation"
    )

    voice_config: Optional[VoiceConfig] = Field(
        None,
        description="Text-to-speech voice configuration"
    )

    quality: Optional[Literal["draft", "standard", "high"]] = Field(
        "standard",
        description="Output audio quality preset affecting processing time"
    )
```

## ADK Agent Documentation

### Agent Class Documentation
```python
from google.adk.agents import Agent, LlmAgent
from google.adk.tools import Tool
from typing import List, Optional

class PodcastSummarizerAgent(LlmAgent):
    """ADK Agent for generating concise podcast summaries.

    This agent specializes in analyzing transcript text and generating
    engaging summaries suitable for audio presentation. It follows ADK
    patterns for tool usage and state management.

    The agent uses a two-pass approach:
    1. Extract key points and themes
    2. Generate conversational summary

    Attributes:
        model: Gemini model used for generation (default: gemini-2.0-flash)
        name: Agent identifier within the pipeline
        summary_style: Output style (conversational, bullet_points, narrative)
        max_summary_length: Maximum length of generated summary

    State Keys:
        transcript_text (str): Input transcript to summarize
        summary_result (str): Generated summary output
        key_points (List[str]): Extracted key discussion points

    Example:
        ```python
        summarizer = PodcastSummarizerAgent(
            name="podcast_summarizer",
            summary_style="conversational",
            instruction="Generate engaging 5-minute podcast summaries"
        )

        # The agent reads from state['transcript_text']
        # and writes to state['summary_result']
        ```

    Note:
        This agent is designed to work within the ADK pipeline framework
        and expects transcript_text to be present in the session state.

    See Also:
        - :class:`TranscriptFetcherAgent`: Provides input transcript
        - :class:`SynthesizerAgent`: Consumes summary for script generation
    """

    def __init__(
        self,
        name: str = "podcast_summarizer",
        model: str = "gemini-2.0-flash",
        summary_style: str = "conversational",
        max_summary_length: int = 2000,
        instruction: Optional[str] = None,
        tools: Optional[List[Tool]] = None,
        **kwargs
    ):
        """Initialize the podcast summarizer agent.

        Args:
            name: Unique identifier for this agent
            model: Gemini model to use for generation
            summary_style: Style of summary to generate:
                - "conversational": Natural dialogue style
                - "bullet_points": Structured key points
                - "narrative": Story-like presentation
            max_summary_length: Maximum characters in generated summary
            instruction: Custom instruction override. If not provided,
                uses default instruction based on summary_style
            tools: Additional tools for the agent to use
            **kwargs: Additional arguments passed to LlmAgent

        Example:
            ```python
            # Custom configuration
            agent = PodcastSummarizerAgent(
                name="technical_summarizer",
                model="gemini-2.0-flash",
                summary_style="bullet_points",
                instruction="Focus on technical details and actionable insights"
            )
            ```
        """
        if instruction is None:
            instruction = self._generate_instruction(summary_style, max_summary_length)

        super().__init__(
            name=name,
            model=model,
            instruction=instruction,
            tools=tools or [],
            output_key="summary_result",  # ADK pattern for state management
            **kwargs
        )

        self.summary_style = summary_style
        self.max_summary_length = max_summary_length
```

### Tool Documentation for ADK
```python
from google.adk.tools import FunctionTool, ToolContext
from typing import Dict, List, Optional

@FunctionTool
def extract_key_topics(
    text: str,
    max_topics: int = 5,
    min_relevance_score: float = 0.7,
    tool_context: ToolContext = None
) -> Dict[str, List[str]]:
    """Extract key topics from transcript text using NLP analysis.

    This tool analyzes transcript text to identify main discussion topics,
    themes, and key points. It uses TF-IDF and semantic clustering to
    ensure relevant topic extraction.

    Args:
        text: Input transcript text to analyze
        max_topics: Maximum number of topics to extract (default: 5)
        min_relevance_score: Minimum relevance score for topic inclusion (0-1)
        tool_context: ADK tool context providing access to state and services

    Returns:
        Dictionary containing:
            - topics (List[str]): Main discussion topics
            - keywords (List[str]): Important keywords and phrases
            - themes (List[str]): Overarching themes identified

    Example:
        When used within an ADK agent::

            # In agent instruction
            instruction = '''
            Use extract_key_topics to identify main themes from the transcript,
            then create a summary focusing on those topics.
            '''

            # Tool automatically receives transcript from state

    Note:
        This tool accesses state['transcript_text'] if text is not provided
        directly, allowing seamless integration with the pipeline.

    Raises:
        ValueError: If text is empty or too short for analysis

    See Also:
        - :func:`generate_summary_outline`: Uses extracted topics
    """
    # Use tool_context to access state if needed
    if not text and tool_context:
        text = tool_context.state.get('transcript_text', '')

    if not text or len(text) < 100:
        raise ValueError("Text too short for meaningful topic extraction")

    # Topic extraction implementation...
    topics = extract_topics_impl(text, max_topics, min_relevance_score)

    # Store intermediate results in state for debugging
    if tool_context:
        tool_context.state['extracted_topics'] = topics

    return topics
```

## Code Comments Guidelines

### When to Use Comments

#### DO Comment
```python
# Business logic explanation
def calculate_discount(user: User, cart_total: float) -> float:
    """Calculate user discount based on loyalty status."""
    # Premium users get 20% off orders over $100 as per Q4 2024 promotion
    if user.is_premium and cart_total > 100:
        return cart_total * 0.2

    # Regular users get 10% off their first order only
    if user.order_count == 0:
        return cart_total * 0.1

    return 0.0

# Complex algorithm explanation
def optimize_audio_segments(segments: List[AudioSegment]) -> List[AudioSegment]:
    """Optimize audio segments for smooth playback."""
    # Use dynamic programming to find optimal segment boundaries
    # that minimize total transition artifacts while maintaining
    # maximum segment duration constraints
    dp = [[float('inf')] * len(segments) for _ in range(len(segments))]

    # Base case: single segments have no transition cost
    for i in range(len(segments)):
        dp[i][i] = 0

    # Fill DP table using transition cost function
    # O(n²) time complexity is acceptable for typical podcast lengths
    for length in range(2, len(segments) + 1):
        for start in range(len(segments) - length + 1):
            end = start + length - 1
            # ... implementation

# TODO/FIXME comments with context
async def process_large_transcript(transcript: str) -> str:
    """Process transcripts that may exceed memory limits."""
    # TODO(john, 2024-Q2): Implement streaming processing for transcripts
    # over 1MB to handle 4+ hour podcasts. See issue #234

    # FIXME: Current implementation loads entire transcript into memory
    # which causes OOM errors on pods with <2GB RAM
    if len(transcript) > 1_000_000:
        logger.warning("Large transcript may cause memory issues")

    return await self._process_impl(transcript)

# Non-obvious behavior
def get_audio_duration(file_path: str) -> float:
    """Get duration of audio file in seconds."""
    # We use mutagen instead of pydub here because pydub loads
    # the entire file into memory, which is problematic for large files
    from mutagen import File

    audio = File(file_path)
    # Mutagen returns None for corrupted files instead of raising
    if audio is None:
        raise ValueError(f"Could not read audio file: {file_path}")

    return audio.info.length
```

#### DON'T Comment
```python
# Obvious variable assignments
user_count = len(users)  # DON'T: Get the number of users

# Self-explanatory code
def get_user_by_id(user_id: int) -> User:
    # DON'T: Query database for user with given ID
    return db.query(User).filter(User.id == user_id).first()

# Redundant comments
# DON'T: Increment counter by 1
counter += 1

# Commented-out code without explanation
# DON'T: Leave dead code
# response = await old_api.fetch(url)
# data = response.json()
```

### Comment Formatting Standards

```python
# Single-line comments: Capitalize first word, no period for short comments
# This is a short comment

# Multi-line comments: Use proper sentences with punctuation.
# This is a longer comment that explains something complex.
# It spans multiple lines and uses proper grammar.

# Section separators for long files
# ============================================================================
# AUTHENTICATION HANDLERS
# ============================================================================

# Inline comments: Space before, lowercase, brief
result = complex_calculation()  # adjust for timezone

# Block comments before code
# The following section handles edge cases for leap years
# in date calculations. We need special logic because...
if is_leap_year(year):
    # ... code
```

### TypeScript Comment Standards
```typescript
// Single-line comments follow same rules as Python
const userCount = users.length;

// Multi-line comments use /* */ for JSDoc, // for regular
/*
 * This is a multi-line comment block that would appear
 * in generated documentation. Use for public APIs.
 */

// Regular multi-line comment for internal notes
// This complex logic handles browser quirks for Safari < 14
// where AudioContext.resume() returns undefined instead
// of a Promise in certain scenarios.

// Section separators
// ============================================================================
// EVENT HANDLERS
// ============================================================================

// TODO format with assignee and date
// TODO(sarah, 2024-03): Migrate to new event system

// Inline comments
const result = calculate(data);  // includes tax
```

## Documentation Tools and Automation

### Python Documentation Generation
```bash
# Sphinx configuration for API docs
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Generate documentation
cd docs
sphinx-apidoc -f -o source/ ../src/
make html

# Validate docstrings with pydocstyle
pip install pydocstyle
pydocstyle src/ --config=.pydocstyle

# .pydocstyle configuration
[pydocstyle]
inherit = false
match = .*\.py
match-dir = [^\.].∗
ignore = D100,D104,D213,D203
```

### TypeScript Documentation Generation
```json
// typedoc.json
{
  "entryPoints": ["src/index.ts"],
  "out": "docs/api",
  "exclude": ["**/*.test.ts", "**/node_modules/**"],
  "includeVersion": true,
  "categorizeByGroup": true,
  "plugin": ["typedoc-plugin-markdown"],
  "readme": "README.md",
  "theme": "default",
  "validation": {
    "notExported": true,
    "invalidLink": true,
    "notDocumented": false
  }
}

// Generate TypeScript docs
npx typedoc

// ESLint rules for JSDoc
{
  "rules": {
    "jsdoc/check-alignment": "error",
    "jsdoc/check-param-names": "error",
    "jsdoc/require-description": "error",
    "jsdoc/require-param-description": "error",
    "jsdoc/require-returns-description": "error"
  }
}
```

### Pre-commit Hooks for Documentation
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pycqa/pydocstyle
    rev: 6.3.0
    hooks:
      - id: pydocstyle
        additional_dependencies: [toml]
        exclude: ^tests/

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.50.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        additional_dependencies:
          - eslint-plugin-jsdoc
```

### Documentation Coverage Report
```python
# scripts/check_doc_coverage.py
"""Check documentation coverage for Python modules."""

import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple

def check_docstring_coverage(file_path: Path) -> Dict[str, List[str]]:
    """Analyze Python file for missing docstrings."""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    missing = {
        'modules': [],
        'classes': [],
        'functions': [],
        'methods': []
    }

    # Check module docstring
    if not ast.get_docstring(tree):
        missing['modules'].append(str(file_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not ast.get_docstring(node):
                missing['classes'].append(f"{file_path}:{node.name}")

        elif isinstance(node, ast.FunctionDef):
            if not ast.get_docstring(node):
                parent = getattr(node, 'parent', None)
                if isinstance(parent, ast.ClassDef):
                    missing['methods'].append(f"{file_path}:{parent.name}.{node.name}")
                else:
                    missing['functions'].append(f"{file_path}:{node.name}")

    return missing

# Run coverage check
if __name__ == "__main__":
    src_path = Path("src")
    all_missing = {}

    for py_file in src_path.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            missing = check_docstring_coverage(py_file)
            for category, items in missing.items():
                all_missing.setdefault(category, []).extend(items)

    # Generate report
    total_missing = sum(len(items) for items in all_missing.values())
    print(f"Documentation Coverage Report")
    print(f"{'='*50}")
    print(f"Total missing docstrings: {total_missing}")

    for category, items in all_missing.items():
        if items:
            print(f"\n{category.title()} missing docstrings ({len(items)}):")
            for item in items[:10]:  # Show first 10
                print(f"  - {item}")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more")
```

## Examples and Templates

### Complete Module Template (Python)
```python
"""Module name - Brief description.

Detailed description of what this module provides, its purpose,
and how it fits into the larger system architecture.

Example:
    Basic usage example::

        from package.module import MainClass

        instance = MainClass()
        result = instance.process(data)

Note:
    Any important notes about module usage, limitations, or requirements.

Attributes:
    MODULE_CONSTANT (type): Description of module-level constant

.. versionadded:: 1.0.0
.. versionchanged:: 1.2.0
   Added support for async operations
"""

from typing import Optional, List, Dict, Any
import logging

# Module-level logger
logger = logging.getLogger(__name__)

# Documented module constants
DEFAULT_TIMEOUT: int = 30
"""Default timeout in seconds for operations."""

__all__ = ['MainClass', 'helper_function', 'CustomError']


class CustomError(Exception):
    """Custom exception for module-specific errors.

    Attributes:
        message: Human-readable error description
        error_code: Numeric error code for categorization
        details: Additional error context
    """

    def __init__(self, message: str, error_code: int, details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class MainClass:
    """Main class implementing core functionality.

    Detailed description of the class purpose and behavior.

    Attributes:
        config: Configuration dictionary
        state: Current processing state

    Example:
        >>> instance = MainClass({"timeout": 60})
        >>> instance.process("data")
        'processed data'
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with optional configuration.

        Args:
            config: Configuration dictionary with keys:
                - timeout (int): Operation timeout in seconds
                - retry_count (int): Number of retries on failure
                - debug (bool): Enable debug logging
        """
        self.config = config or {}
        self.state = "initialized"

    async def process(self, data: str) -> str:
        """Process input data asynchronously.

        Args:
            data: Input data to process

        Returns:
            Processed data string

        Raises:
            CustomError: If processing fails
            ValueError: If data is invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")

        try:
            # Processing logic with explanatory comments
            result = await self._internal_process(data)
            self.state = "completed"
            return result
        except Exception as e:
            self.state = "failed"
            raise CustomError(
                f"Processing failed: {str(e)}",
                error_code=500,
                details={"input": data}
            )


def helper_function(value: int, multiplier: float = 1.0) -> float:
    """Helper function with clear purpose.

    Args:
        value: Base integer value
        multiplier: Optional multiplier (default: 1.0)

    Returns:
        Calculated result as float

    Example:
        >>> helper_function(10, 2.5)
        25.0
    """
    return value * multiplier
```

### Complete Component Template (TypeScript)
```typescript
/**
 * @fileoverview Audio visualization component with waveform display.
 *
 * Provides interactive audio playback with visual waveform representation,
 * seeking capabilities, and playback controls.
 *
 * @module components/AudioVisualizer
 * @requires react
 * @requires @/hooks/useAudio
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAudio } from '@/hooks/useAudio';
import type { AudioVisualizerProps, WaveformData } from '@/types/audio';

/**
 * Default configuration for the audio visualizer.
 * @constant
 */
const DEFAULT_CONFIG = {
  waveformHeight: 128,
  waveformColor: '#3b82f6',
  progressColor: '#1d4ed8',
  barWidth: 2,
  barGap: 1,
} as const;

/**
 * Audio visualizer component with waveform display.
 *
 * Renders an interactive audio player with waveform visualization,
 * supporting seeking, playback control, and real-time progress updates.
 *
 * @component
 * @example
 * ```tsx
 * // Basic usage
 * <AudioVisualizer src="/audio/podcast.mp3" />
 *
 * // With custom styling and callbacks
 * <AudioVisualizer
 *   src="/audio/podcast.mp3"
 *   height={200}
 *   waveformColor="#10b981"
 *   onPlayStateChange={(playing) => console.log('Playing:', playing)}
 *   onTimeUpdate={(time) => console.log('Current time:', time)}
 * />
 * ```
 *
 * @param {AudioVisualizerProps} props - Component properties
 * @returns {JSX.Element} Rendered audio visualizer
 *
 * @since 1.0.0
 */
export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  src,
  height = DEFAULT_CONFIG.waveformHeight,
  waveformColor = DEFAULT_CONFIG.waveformColor,
  progressColor = DEFAULT_CONFIG.progressColor,
  barWidth = DEFAULT_CONFIG.barWidth,
  barGap = DEFAULT_CONFIG.barGap,
  onPlayStateChange,
  onTimeUpdate,
  onError,
  className,
  ...rest
}) => {
  // State management with descriptive names
  const [isLoading, setIsLoading] = useState(true);
  const [waveformData, setWaveformData] = useState<WaveformData | null>(null);

  // Custom hook for audio management
  const {
    audioRef,
    isPlaying,
    currentTime,
    duration,
    play,
    pause,
    seek,
  } = useAudio(src, {
    onError: (error) => {
      setIsLoading(false);
      onError?.(error);
    },
  });

  /**
   * Generates waveform visualization data from audio buffer.
   * Uses Web Audio API for frequency analysis.
   */
  const generateWaveform = useCallback(async () => {
    try {
      setIsLoading(true);

      // Fetch and decode audio data
      const response = await fetch(src);
      const arrayBuffer = await response.arrayBuffer();
      const audioContext = new AudioContext();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

      // Extract waveform data with downsampling for performance
      const data = extractWaveformData(audioBuffer, {
        targetBars: Math.floor(width / (barWidth + barGap)),
        normalize: true,
      });

      setWaveformData(data);
    } catch (error) {
      console.error('Failed to generate waveform:', error);
      onError?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [src, barWidth, barGap, onError]);

  // Generate waveform on mount and src change
  useEffect(() => {
    generateWaveform();
  }, [generateWaveform]);

  /**
   * Handles click on waveform for seeking.
   * Calculates time based on click position.
   */
  const handleWaveformClick = useCallback(
    (event: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = event.currentTarget;
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const seekTime = (x / rect.width) * duration;

      seek(seekTime);
    },
    [duration, seek]
  );

  // Render loading state
  if (isLoading) {
    return (
      <div className={`audio-visualizer-loading ${className}`} {...rest}>
        <div className="spinner" />
        <span>Loading audio...</span>
      </div>
    );
  }

  // Main render
  return (
    <div className={`audio-visualizer ${className}`} {...rest}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onClick={handleWaveformClick}
        className="waveform-canvas"
      />

      <div className="controls">
        <button
          onClick={isPlaying ? pause : play}
          className="play-pause-button"
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? <PauseIcon /> : <PlayIcon />}
        </button>

        <div className="time-display">
          <span>{formatTime(currentTime)}</span>
          <span>/</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  );
};

/**
 * Props for the AudioVisualizer component.
 *
 * @interface AudioVisualizerProps
 * @extends {React.HTMLAttributes<HTMLDivElement>}
 */
export interface AudioVisualizerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Audio file URL or path */
  src: string;

  /** Height of the waveform canvas in pixels */
  height?: number;

  /** Color of the waveform bars */
  waveformColor?: string;

  /** Color of the progress indicator */
  progressColor?: string;

  /** Width of each waveform bar in pixels */
  barWidth?: number;

  /** Gap between waveform bars in pixels */
  barGap?: number;

  /** Callback fired when play state changes */
  onPlayStateChange?: (isPlaying: boolean) => void;

  /** Callback fired on time update during playback */
  onTimeUpdate?: (currentTime: number) => void;

  /** Callback fired when an error occurs */
  onError?: (error: Error) => void;
}

/**
 * Formats time in seconds to MM:SS display format.
 *
 * @param {number} seconds - Time in seconds
 * @returns {string} Formatted time string
 *
 * @example
 * ```typescript
 * formatTime(125); // "2:05"
 * formatTime(3661); // "61:01"
 * ```
 */
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Additional helper functions...
```

## Documentation Review Checklist

### Before Code Review
- [ ] All public APIs have complete docstrings/JSDoc
- [ ] Complex algorithms have explanatory comments
- [ ] Type annotations are complete and accurate
- [ ] Examples are provided for non-trivial usage
- [ ] Edge cases and exceptions are documented
- [ ] Breaking changes are clearly marked
- [ ] Links to related documentation are included

### During Development
- [ ] Update docstrings when changing function signatures
- [ ] Add comments for non-obvious business logic
- [ ] Document any workarounds or temporary solutions
- [ ] Include references to issue numbers for TODOs
- [ ] Ensure examples still work after changes

### Documentation Quality Metrics
- Docstring coverage: >95% for public APIs
- Comment density: 15-25% for complex modules
- Example coverage: All public classes and key functions
- Update frequency: Documentation updated with code

## Enforcement and Validation

### CI/CD Integration
```yaml
# .github/workflows/documentation.yml
name: Documentation Validation

on: [push, pull_request]

jobs:
  validate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pydocstyle sphinx
          npm install -g typedoc eslint eslint-plugin-jsdoc

      - name: Check Python docstrings
        run: pydocstyle src/ --config=.pydocstyle

      - name: Check TypeScript JSDoc
        run: |
          cd client
          eslint src/ --ext .ts,.tsx

      - name: Generate documentation
        run: |
          sphinx-build -b html docs/source docs/build
          cd client && typedoc

      - name: Check documentation coverage
        run: python scripts/check_doc_coverage.py --min-coverage 95
```

This comprehensive documentation standard ensures high-quality, maintainable code documentation across the entire Podcast Digest Agent project.
