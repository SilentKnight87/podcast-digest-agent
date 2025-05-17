from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
import uuid

# --- Common Models ---
class ConfigOption(BaseModel):
    name: str
    value: str

# --- /config Endpoint --- 
class ApiConfigResponse(BaseModel):
    available_tts_voices: List[ConfigOption]
    available_summary_lengths: List[ConfigOption]
    available_audio_styles: List[ConfigOption]

# --- /process_youtube_url Endpoint --- 
class ProcessUrlRequest(BaseModel):
    youtube_url: HttpUrl = Field(..., description="The URL of the YouTube video to process.")
    summary_length: Optional[str] = Field(default=None, description="Desired summary length (e.g., short, medium, long).")
    tts_voice: Optional[str] = Field(default=None, description="TTS voice to use for the audio digest.")
    audio_style: Optional[str] = Field(default=None, description="Desired audio style for the digest.")

class VideoDetails(BaseModel):
    title: str = "Unknown Title"
    thumbnail: Optional[HttpUrl] = None
    channel_name: str = "Unknown Channel"
    duration: Optional[int] = Field(default=None, description="Duration in seconds") # In seconds
    url: Optional[HttpUrl] = Field(default=None, description="The full URL of the YouTube video.")
    upload_date: Optional[str] = Field(default=None, description="The upload date of the video (e.g., YYYY-MM-DD).")

class ProcessUrlResponse(BaseModel):
    task_id: str = Field(description="Unique ID for the processing task.")
    status: str = Field(default="queued", description="Initial status of the task.")
    video_details: Optional[VideoDetails] = None

# --- /status/{task_id} Endpoint ---
class AgentLog(BaseModel):
    timestamp: str
    level: str
    message: str

class AgentNode(BaseModel):
    id: str
    name: str
    description: str
    type: str # e.g., "transcription", "summarization", "tts"
    status: str # 'pending' | 'running' | 'completed' | 'error'
    progress: float = Field(default=0.0, ge=0, le=100) # 0-100
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    icon: str # Lucide icon name or similar identifier
    logs: Optional[List[AgentLog]] = None
    metrics: Optional[Dict[str, Any]] = None

class DataFlow(BaseModel):
    id: str
    from_agent_id: str
    to_agent_id: str
    data_type: str # e.g., "transcript", "summary", "audio_script"
    status: str # 'pending' | 'transferring' | 'completed' | 'error'
    metadata: Optional[Dict[str, Any]] = {}

class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str # e.g., "TASK_STARTED", "AGENT_COMPLETED", "ERROR"
    message: str
    agent_id: Optional[str] = None

class ProcessingStatus(BaseModel):
    overall_progress: float = Field(default=0.0, ge=0, le=100)
    status: str # "queued", "processing", "completed", "failed"
    current_agent_id: Optional[str] = None
    start_time: Optional[str] = None
    estimated_end_time: Optional[str] = None
    elapsed_time: Optional[str] = None # e.g., "00:11:30"
    remaining_time: Optional[str] = None # e.g., "00:03:30"

class TaskStatusResponse(BaseModel):
    task_id: str
    processing_status: ProcessingStatus
    agents: List[AgentNode]
    data_flows: List[DataFlow]
    timeline: List[TimelineEvent]
    # Results (available when completed)
    summary_text: Optional[str] = None
    audio_file_url: Optional[str] = None
    error_message: Optional[str] = None

# --- /history Endpoint ---
class AudioOutput(BaseModel):
    url: str
    duration: str # e.g., "00:03:28"
    file_size: str # e.g., "3.2MB"

class SummaryContent(BaseModel):
    title: str
    host: Optional[str] = None
    main_points: List[str]
    highlights: List[str]
    key_quotes: List[str]

class HistoryTaskItem(BaseModel):
    task_id: str
    video_details: VideoDetails 
    completion_time: str # ISO format timestamp
    processing_duration: str # e.g., "00:15:42"
    audio_output: Optional[AudioOutput] = None # Changed to Optional as per test_history_task_item_with_error
    summary: Optional[SummaryContent] = None      # Changed to Optional as per test_history_task_item_with_error
    error_message: Optional[str] = None

class TaskHistoryResponse(BaseModel):
    tasks: List[HistoryTaskItem]
    total_tasks: int
    limit: int
    offset: int

# --- General --- 
class MessageResponse(BaseModel):
    message: str 