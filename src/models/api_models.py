from typing import Any

from pydantic import BaseModel, Field, HttpUrl


# --- Common Models ---
class ConfigOption(BaseModel):
    id: str
    name: str
    description: str | None = None
    language: str | None = None
    type: str | None = None
    preview_url: str | None = None  # Changed from HttpUrl to str to allow relative URLs


# --- /config Endpoint ---
class ApiConfigResponse(BaseModel):
    available_tts_voices: list[ConfigOption] = Field(..., alias="availableTtsVoices")
    available_summary_lengths: list[ConfigOption] = Field(..., alias="availableSummaryLengths")
    available_audio_styles: list[ConfigOption] = Field(..., alias="availableAudioStyles")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "availableTtsVoices": [
                    {
                        "id": "standard_voice_1",
                        "name": "Standard Voice 1 (Female)",
                        "language": "en-US",
                        "type": "Standard",
                    },
                    {
                        "id": "neural_voice_1",
                        "name": "Neural Voice 1 (Female)",
                        "language": "en-US",
                        "type": "Neural",
                        "preview_url": "/audio/previews/neural_voice_1.mp3",
                    },
                ],
                "availableSummaryLengths": [
                    {
                        "id": "short",
                        "name": "Short (1-2 mins)",
                        "description": "Brief overview, key takeaways only.",
                    }
                ],
                "availableAudioStyles": [
                    {
                        "id": "informative",
                        "name": "Informative",
                        "description": "Clear, neutral tone suitable for educational content.",
                    }
                ],
            }
        }


# --- /process_youtube_url Endpoint ---
class ProcessUrlRequest(BaseModel):
    youtube_url: HttpUrl = Field(..., description="The URL of the YouTube video to process.")
    summary_length: str | None = Field(
        default=None, description="Desired summary length (e.g., short, medium, long)."
    )
    tts_voice: str | None = Field(
        default=None, description="TTS voice to use for the audio digest."
    )
    audio_style: str | None = Field(default=None, description="Desired audio style for the digest.")


class VideoDetails(BaseModel):
    title: str = "Unknown Title"
    thumbnail: HttpUrl | None = None
    channel_name: str = "Unknown Channel"
    duration: int | None = Field(default=None, description="Duration in seconds")  # In seconds
    url: HttpUrl | None = Field(default=None, description="The full URL of the YouTube video.")
    upload_date: str | None = Field(
        default=None, description="The upload date of the video (e.g., YYYY-MM-DD)."
    )


class ProcessUrlResponse(BaseModel):
    task_id: str = Field(description="Unique ID for the processing task.")
    status: str = Field(default="queued", description="Initial status of the task.")
    video_details: VideoDetails | None = None


# --- /status/{task_id} Endpoint ---
class AgentLog(BaseModel):
    timestamp: str
    level: str
    message: str


class AgentNode(BaseModel):
    id: str
    name: str
    description: str
    type: str  # e.g., "transcription", "summarization", "tts"
    status: str  # 'pending' | 'running' | 'completed' | 'error'
    progress: float = Field(default=0.0, ge=0, le=100)  # 0-100
    start_time: str | None = None
    end_time: str | None = None
    icon: str  # Lucide icon name or similar identifier
    logs: list[AgentLog] | None = None
    metrics: dict[str, Any] | None = None


class DataFlow(BaseModel):
    id: str
    from_agent_id: str
    to_agent_id: str
    data_type: str  # e.g., "transcript", "summary", "audio_script"
    status: str  # 'pending' | 'transferring' | 'completed' | 'error'
    metadata: dict[str, Any] | None = {}


class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str  # e.g., "TASK_STARTED", "AGENT_COMPLETED", "ERROR"
    message: str
    agent_id: str | None = None


class ProcessingStatus(BaseModel):
    overall_progress: float = Field(default=0.0, ge=0, le=100)
    status: str  # "queued", "processing", "completed", "failed"
    current_agent_id: str | None = None
    start_time: str | None = None
    estimated_end_time: str | None = None
    elapsed_time: str | None = None  # e.g., "00:11:30"
    remaining_time: str | None = None  # e.g., "00:03:30"


class TaskStatusResponse(BaseModel):
    task_id: str
    processing_status: ProcessingStatus
    agents: list[AgentNode]
    data_flows: list[DataFlow]
    timeline: list[TimelineEvent]
    # Results (available when completed)
    summary_text: str | None = None
    audio_file_url: str | None = None
    error_message: str | None = None


# --- /history Endpoint ---
class AudioOutput(BaseModel):
    url: str
    duration: str  # e.g., "00:03:28"
    file_size: str  # e.g., "3.2MB"


class SummaryContent(BaseModel):
    title: str
    host: str | None = None
    main_points: list[str]
    highlights: list[str]
    key_quotes: list[str]


class HistoryTaskItem(BaseModel):
    task_id: str
    video_details: VideoDetails
    completion_time: str  # ISO format timestamp
    processing_duration: str  # e.g., "00:15:42"
    audio_output: AudioOutput | None = (
        None  # Changed to Optional as per test_history_task_item_with_error
    )
    summary: SummaryContent | None = (
        None  # Changed to Optional as per test_history_task_item_with_error
    )
    error_message: str | None = None


class TaskHistoryResponse(BaseModel):
    tasks: list[HistoryTaskItem]
    total_tasks: int
    limit: int
    offset: int


# --- General ---
class MessageResponse(BaseModel):
    message: str
