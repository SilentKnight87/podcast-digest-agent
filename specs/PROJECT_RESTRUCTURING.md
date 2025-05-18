# Project Restructuring Specification

## Overview

This specification outlines a comprehensive plan for restructuring the Podcast Digest Agent project to follow modern software architecture best practices, improve maintainability, and prepare for future growth. The restructuring will address the organization of both the backend (Python/FastAPI) and frontend (Next.js) components.

## Goals

1. Implement clear separation of concerns
2. Establish consistent naming conventions
3. Improve modularity and testability
4. Reduce coupling between components
5. Facilitate easier onboarding for new developers
6. Prepare the codebase for future scaling
7. Optimize for long-term maintainability

## Current Structure Analysis

### Backend (Python/FastAPI)

Current structure:

```
src/
  __init__.py
  agents/
    __init__.py
    audio_generator.py
    base_agent.py
    summarizer.py
    synthesizer.py
    transcript_fetcher.py
  api/
    v1/
      endpoints/
        audio.py
        config.py
        tasks.py
      router.py
  config/
    __init__.py
    logging_config.py
    settings.py
  core/
    connection_manager.py
    task_manager.py
  main.py
  models/
    api_models.py
  podcast_digest_agent.egg-info/
  processing/
    pipeline.py
  runners/
    __init__.py
    pipeline_runner.py
  sessions/
    __init__.py
  tools/
    __init__.py
    audio_tools.py
    summarization_tools.py
    synthesis_tools.py
    transcript_tools.py
  utils/
    __init__.py
    base_tool.py
    input_processor.py
```

Issues:
- Mixed responsibilities within modules
- Inconsistent naming conventions
- Insufficient separation between domain and infrastructure
- Unclear boundaries between components
- Limited visibility into the system's architecture from the file structure

### Frontend (Next.js)

Current structure:

```
podcast-digest-ui/
  README.md
  components.json
  eslint.config.mjs
  mock_data.json
  next-env.d.ts
  next.config.ts
  package-lock.json
  package.json
  postcss.config.mjs
  public/
    file.svg
    globe.svg
    next.svg
    vercel.svg
    window.svg
  src/
    app/
      globals.css
      layout.tsx
      page.tsx
    components/
      Hero/
        HeroSection.tsx
        PlayDigestButton.tsx
      Layout/
        Footer.tsx
        Navbar.tsx
        query-provider.tsx
        theme-provider.tsx
        theme-toggle.tsx
      Process/
        ProcessTimeline.tsx
        ProcessingVisualizer.tsx
      Results/
      ui/
        Waveform.tsx
        button.tsx
        input.tsx
        sonner.tsx
    contexts/
      AgentWorkflowContext.tsx
      WorkflowContext.tsx
    lib/
    types/
      index.ts
      workflow.ts
  tailwind.config.ts
  tsconfig.json
```

Issues:
- Flat component hierarchy without clear domain separation
- Context implementation without clear boundaries
- Missing API integration structure
- Insufficient type definitions
- Inconsistent component organization

## Proposed Restructuring

### Backend Restructuring

#### New Backend Structure

```
podcast_digest_agent/  # Root package name (Python convention)
  __init__.py
  api/  # API layer
    __init__.py
    dependencies.py  # FastAPI dependencies
    error_handlers.py  # Global error handlers
    routers/  # API routers
      __init__.py
      audio.py
      config.py
      tasks.py
      websocket.py
    schemas/  # API request/response models
      __init__.py
      audio.py
      config.py
      task.py
  core/  # Core domain logic
    __init__.py
    agents/  # Agent interfaces and base classes
      __init__.py
      base.py
      registry.py
    models/  # Domain models
      __init__.py
      audio.py
      task.py
      transcript.py
    pipeline/  # Pipeline management
      __init__.py
      coordinator.py
      runner.py
    services/  # Domain services
      __init__.py
      task_service.py
      websocket_service.py
  domain/  # Domain implementations
    __init__.py
    audio/  # Audio generation
      __init__.py
      generator.py
      models.py
      tools.py
    summarization/  # Summarization
      __init__.py
      models.py
      summarizer.py
      tools.py
    synthesis/  # Dialogue synthesis
      __init__.py
      models.py
      synthesizer.py
      tools.py
    transcript/  # Transcript fetching
      __init__.py
      fetcher.py
      models.py
      tools.py
  infrastructure/  # External dependencies
    __init__.py
    ai/  # AI providers
      __init__.py
      google_ai.py
      openai.py
    storage/  # Storage providers
      __init__.py
      file_system.py
    tts/  # Text-to-speech providers
      __init__.py
      google_tts.py
  config/  # Configuration
    __init__.py
    logging.py
    settings.py
  utils/  # Utilities
    __init__.py
    errors.py
    helpers.py
    validation.py
  main.py  # Application entry point
```

### Frontend Restructuring

#### New Frontend Structure

```
podcast-digest-ui/
  public/  # Static assets
    audio/  # Sample audio files
    icons/  # SVG icons
    images/  # Images
  src/
    app/  # Next.js app router
      (auth)/  # Authentication routes (grouped)
        login/
          page.tsx
        register/
          page.tsx
      (dashboard)/  # Dashboard routes (grouped)
        history/
          page.tsx
        settings/
          page.tsx
      api/  # API routes for the frontend
        auth/
          [...nextauth].ts
      globals.css
      layout.tsx
      page.tsx
    components/  # UI components
      auth/  # Authentication components
        login-form.tsx
        register-form.tsx
      common/  # Shared components
        alerts/
          error-alert.tsx
          success-alert.tsx
        buttons/
          primary-button.tsx
          secondary-button.tsx
        forms/
          form-field.tsx
          input.tsx
          text-area.tsx
        layout/
          container.tsx
          footer.tsx
          header.tsx
          navbar.tsx
        modals/
          confirmation-modal.tsx
          dialog.tsx
      digest/  # Digest-specific components
        audio-player.tsx
        digest-card.tsx
        digest-details.tsx
      pipeline/  # Pipeline visualization
        agent-card.tsx
        agent-details.tsx
        data-flow.tsx
        pipeline-visualizer.tsx
        progress-timeline.tsx
    config/  # Application configuration
      constants.ts
      routes.ts
      theme.ts
    contexts/  # React contexts
      auth-context.tsx
      theme-context.tsx
      workflow-context.tsx
    hooks/  # Custom React hooks
      use-audio-player.ts
      use-fetch.ts
      use-form.ts
      use-workflow.ts
    lib/  # Libraries and utilities
      api/  # API integration
        api-client.ts
        endpoints.ts
        websocket-manager.ts
      utils/  # Utility functions
        date-formatter.ts
        string-utils.ts
        validation.ts
    providers/  # Context providers
      providers.tsx  # Combined providers for app
    styles/  # CSS modules and styles
      animations.css
      variables.css
    types/  # TypeScript type definitions
      api.ts  # API types
      auth.ts  # Authentication types
      components.ts  # Component prop types
      workflow.ts  # Workflow types
  .env.local.example  # Environment variables example
  .eslintrc.js  # ESLint configuration
  .prettierrc.js  # Prettier configuration
  next.config.mjs  # Next.js configuration
  package.json  # Dependencies
  postcss.config.js  # PostCSS configuration
  tailwind.config.js  # Tailwind CSS configuration
  tsconfig.json  # TypeScript configuration
```

## Implementation Details

### 1. Backend Restructuring Implementation

#### 1.1 Create New Package Structure

1. Create the new directory structure while preserving the existing code
2. Set up `__init__.py` files to define package exports

```python
# podcast_digest_agent/__init__.py
"""Podcast Digest Agent - A system for processing YouTube podcasts into audio digests."""

__version__ = "0.1.0"
```

#### 1.2 Move and Reorganize Agents

1. Move the agent implementations to the domain directory
2. Create base agent interfaces in the core directory

```python
# podcast_digest_agent/core/agents/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T_Input = TypeVar("T_Input")
T_Output = TypeVar("T_Output")

class BaseAgent(Generic[T_Input, T_Output], ABC):
    """Base interface for all agents in the system."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of the agent."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get the description of the agent."""
        pass
    
    @abstractmethod
    async def process(self, input_data: T_Input) -> T_Output:
        """Process the input data and return the output."""
        pass
    
    @abstractmethod
    async def stream_process(self, input_data: T_Input):
        """Process the input data and yield progress updates."""
        pass
```

```python
# podcast_digest_agent/domain/transcript/fetcher.py
from podcast_digest_agent.core.agents.base import BaseAgent
from podcast_digest_agent.domain.transcript.models import TranscriptInput, TranscriptOutput
from podcast_digest_agent.domain.transcript.tools import FetchTranscriptTool

class TranscriptFetcher(BaseAgent[TranscriptInput, TranscriptOutput]):
    """Agent responsible for fetching transcripts from YouTube videos."""
    
    @property
    def name(self) -> str:
        return "Transcript Fetcher"
    
    @property
    def description(self) -> str:
        return "Fetches transcripts from YouTube videos."
    
    def __init__(self):
        self.fetch_tool = FetchTranscriptTool()
    
    async def process(self, input_data: TranscriptInput) -> TranscriptOutput:
        """Fetch transcript from YouTube video."""
        # Implementation
        
    async def stream_process(self, input_data: TranscriptInput):
        """Fetch transcript with progress updates."""
        # Implementation with yield statements
```

#### 1.3 Implement Domain Models

Create domain models to represent core entities:

```python
# podcast_digest_agent/core/models/task.py
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    """Status of a processing task."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentStatus(str, Enum):
    """Status of an agent in a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"

class AgentInfo(BaseModel):
    """Information about an agent in a task."""
    id: str
    name: str
    status: AgentStatus = AgentStatus.PENDING
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ProcessingStatus(BaseModel):
    """Status of a processing task."""
    status: TaskStatus = TaskStatus.QUEUED
    overall_progress: float = 0.0
    current_agent_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class Task(BaseModel):
    """A processing task in the system."""
    task_id: str
    youtube_url: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    processing_status: ProcessingStatus = Field(default_factory=ProcessingStatus)
    agents: List[AgentInfo] = []
    video_details: Optional[Dict] = None
    summary_text: Optional[str] = None
    audio_url: Optional[str] = None
```

#### 1.4 Create API Schemas

Separate API schemas from domain models:

```python
# podcast_digest_agent/api/schemas/task.py
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, HttpUrl

class ProcessUrlRequest(BaseModel):
    """Request to process a YouTube URL."""
    youtube_url: HttpUrl
    summary_length: Optional[str] = None
    audio_style: Optional[str] = None
    tts_voice: Optional[str] = None

class ProcessUrlResponse(BaseModel):
    """Response after submitting a URL for processing."""
    task_id: str
    status: str

class AgentStatusResponse(BaseModel):
    """Status of an agent in a task."""
    id: str
    name: str
    status: str
    progress: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class ProcessingStatusResponse(BaseModel):
    """Status of a processing task."""
    status: str
    overall_progress: float
    current_agent_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class VideoDetailsResponse(BaseModel):
    """Details of a YouTube video."""
    title: str
    thumbnail: str
    channel_name: str
    duration: int
    upload_date: str
    url: str

class TaskStatusResponse(BaseModel):
    """Full status of a processing task."""
    task_id: str
    processing_status: ProcessingStatusResponse
    agents: List[AgentStatusResponse]
    video_details: Optional[VideoDetailsResponse] = None
    summary_text: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

#### 1.5 Implement Core Services

Create service classes for business logic:

```python
# podcast_digest_agent/core/services/task_service.py
from typing import List, Optional
from uuid import uuid4

from podcast_digest_agent.core.models.task import Task, TaskStatus
from podcast_digest_agent.core.pipeline.coordinator import PipelineCoordinator

class TaskService:
    """Service for managing processing tasks."""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self.pipeline_coordinator = PipelineCoordinator()
    
    def create_task(self, youtube_url: str, options: Optional[Dict] = None) -> Task:
        """Create a new processing task."""
        task_id = str(uuid4())
        task = Task(task_id=task_id, youtube_url=youtube_url)
        self._tasks[task_id] = task
        
        # Start processing asynchronously
        self.pipeline_coordinator.start_pipeline(task)
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks."""
        return list(self._tasks.values())
    
    def get_completed_tasks(self, limit: int = 10, offset: int = 0) -> List[Task]:
        """Get completed tasks with pagination."""
        completed_tasks = [
            task for task in self._tasks.values()
            if task.processing_status.status == TaskStatus.COMPLETED
        ]
        # Sort by completion time (end_time)
        completed_tasks.sort(
            key=lambda t: t.processing_status.end_time or t.created_at,
            reverse=True
        )
        return completed_tasks[offset:offset + limit]
    
    def update_task_status(self, task_id: str, status: TaskStatus, **kwargs) -> Optional[Task]:
        """Update the status of a task."""
        task = self.get_task(task_id)
        if not task:
            return None
            
        task.processing_status.status = status
        for key, value in kwargs.items():
            setattr(task.processing_status, key, value)
            
        return task
```

### 2. Frontend Restructuring Implementation

#### 2.1 Create New Directory Structure

1. Set up the new directory structure
2. Create empty files for component organization

#### 2.2 Implement API Integration

Create a proper API client:

```typescript
// src/lib/api/api-client.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

// Get API URL from environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Add global error handling here
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default apiClient;
```

```typescript
// src/lib/api/endpoints.ts
import apiClient from './api-client';
import type { 
  ProcessUrlRequest, 
  ProcessUrlResponse,
  TaskStatusResponse,
  ApiConfigResponse,
  TaskHistoryResponse 
} from '@/types/api';

export const api = {
  // Configuration
  getConfig: async (): Promise<ApiConfigResponse> => {
    const response = await apiClient.get('/config');
    return response.data;
  },
  
  // Processing
  processYoutubeUrl: async (data: ProcessUrlRequest): Promise<ProcessUrlResponse> => {
    const response = await apiClient.post('/process_youtube_url', data);
    return response.data;
  },
  
  // Status
  getTaskStatus: async (taskId: string): Promise<TaskStatusResponse> => {
    const response = await apiClient.get(`/status/${taskId}`);
    return response.data;
  },
  
  // History
  getTaskHistory: async (limit = 10, offset = 0): Promise<TaskHistoryResponse> => {
    const response = await apiClient.get(`/history?limit=${limit}&offset=${offset}`);
    return response.data;
  },
  
  // Audio
  getAudioUrl: (fileName: string): string => {
    return `${apiClient.defaults.baseURL}/audio/${fileName}`;
  },
};
```

#### 2.3 Create WebSocket Manager

```typescript
// src/lib/api/websocket-manager.ts
import { TaskStatusResponse } from '@/types/api';

type WebSocketCallback = (data: TaskStatusResponse) => void;

class WebSocketManager {
  private socket: WebSocket | null = null;
  private callbacks: WebSocketCallback[] = [];
  private taskId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1 second initial delay
  
  // Get WebSocket URL from environment variable
  private baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  connect(taskId: string): void {
    this.taskId = taskId;
    this.reconnectAttempts = 0;
    
    this.connectWebSocket();
  }
  
  private connectWebSocket(): void {
    if (this.socket) {
      this.socket.close();
    }
    
    // Determine protocol (ws or wss) based on API URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${wsProtocol}://${this.baseUrl.replace(/^https?:\/\//, '')}/api/v1/ws/status/${this.taskId}`;
    
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };
    
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskStatusResponse;
        this.callbacks.forEach(callback => callback(data));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.socket.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      
      // Attempt to reconnect if not closed intentionally
      if (this.taskId && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
          this.connectWebSocket();
        }, delay);
      }
    };
    
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  disconnect(): void {
    if (this.socket) {
      this.socket.close(1000, 'Client disconnected');
      this.socket = null;
    }
    this.taskId = null;
    this.callbacks = [];
  }
  
  subscribe(callback: WebSocketCallback): () => void {
    this.callbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      this.callbacks = this.callbacks.filter(cb => cb !== callback);
    };
  }
  
  sendPing(): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send('ping');
    }
  }
}

// Export singleton instance
export const websocketManager = new WebSocketManager();
```

#### 2.4 Create Custom Hooks

```typescript
// src/hooks/use-workflow.ts
import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api/endpoints';
import { websocketManager } from '@/lib/api/websocket-manager';
import type { TaskStatusResponse, ProcessUrlRequest } from '@/types/api';

export function useWorkflow() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Connect to WebSocket when taskId changes
  useEffect(() => {
    if (!taskId) return;
    
    // Initial task status
    api.getTaskStatus(taskId)
      .then(setTaskStatus)
      .catch(err => {
        console.error('Error fetching task status:', err);
        setError('Failed to fetch task status');
      });
    
    // Connect WebSocket
    websocketManager.connect(taskId);
    
    // Subscribe to updates
    const unsubscribe = websocketManager.subscribe((data) => {
      setTaskStatus(data);
      
      // Update processing state based on status
      if (data.processing_status.status === 'completed' || 
          data.processing_status.status === 'failed') {
        setIsProcessing(false);
      }
    });
    
    // Cleanup on unmount
    return () => {
      unsubscribe();
      websocketManager.disconnect();
    };
  }, [taskId]);
  
  // Start processing a new URL
  const startProcessing = useCallback(async (request: ProcessUrlRequest) => {
    try {
      setError(null);
      setIsProcessing(true);
      
      const response = await api.processYoutubeUrl(request);
      setTaskId(response.task_id);
      
      return response.task_id;
    } catch (err) {
      console.error('Error starting processing:', err);
      setError('Failed to start processing');
      setIsProcessing(false);
      throw err;
    }
  }, []);
  
  return {
    taskId,
    taskStatus,
    isProcessing,
    error,
    startProcessing,
  };
}
```

```typescript
// src/hooks/use-audio-player.ts
import { useState, useEffect, useRef } from 'react';

interface AudioPlayerOptions {
  autoplay?: boolean;
  onEnded?: () => void;
}

export function useAudioPlayer(initialUrl?: string, options: AudioPlayerOptions = {}) {
  const [audioUrl, setAudioUrl] = useState<string | null>(initialUrl || null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // Initialize audio element
  useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;
    
    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };
    
    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };
    
    const handleEnded = () => {
      setIsPlaying(false);
      if (options.onEnded) {
        options.onEnded();
      }
    };
    
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', handleEnded);
    
    if (audioUrl) {
      audio.src = audioUrl;
      if (options.autoplay) {
        audio.play().catch(err => console.error('Error autoplaying audio:', err));
      }
    }
    
    return () => {
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('ended', handleEnded);
      audio.pause();
      audio.src = '';
    };
  }, []);
  
  // Update audio source when URL changes
  useEffect(() => {
    if (!audioRef.current || !audioUrl) return;
    
    audioRef.current.src = audioUrl;
    audioRef.current.load();
    
    if (options.autoplay) {
      audioRef.current.play().catch(err => console.error('Error autoplaying audio:', err));
    }
  }, [audioUrl, options.autoplay]);
  
  // Play/pause controls
  const togglePlay = () => {
    if (!audioRef.current) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(err => console.error('Error playing audio:', err));
    }
    
    setIsPlaying(!isPlaying);
  };
  
  // Seek to a specific time
  const seek = (time: number) => {
    if (!audioRef.current) return;
    
    audioRef.current.currentTime = time;
    setCurrentTime(time);
  };
  
  // Set playback rate
  const changePlaybackRate = (rate: number) => {
    if (!audioRef.current) return;
    
    audioRef.current.playbackRate = rate;
    setPlaybackRate(rate);
  };
  
  return {
    audioUrl,
    setAudioUrl,
    isPlaying,
    duration,
    currentTime,
    playbackRate,
    togglePlay,
    seek,
    changePlaybackRate,
  };
}
```

#### 2.5 Refactor Components

Organize components by domain and responsibility:

```tsx
// src/components/digest/audio-player.tsx
import { useState, useEffect } from 'react';
import { useAudioPlayer } from '@/hooks/use-audio-player';

interface AudioPlayerProps {
  audioUrl: string;
  transcript?: string;
}

export function AudioPlayer({ audioUrl, transcript }: AudioPlayerProps) {
  const {
    isPlaying,
    duration,
    currentTime,
    playbackRate,
    togglePlay,
    seek,
    changePlaybackRate,
  } = useAudioPlayer(audioUrl);
  
  const [showTranscript, setShowTranscript] = useState(true);
  
  // Format time as mm:ss
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Calculate progress percentage
  const progressPercent = duration ? (currentTime / duration) * 100 : 0;
  
  return (
    <div className="audio-player">
      <div className="audio-controls">
        <button 
          className="play-button" 
          onClick={togglePlay}
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? '⏸️' : '▶️'}
        </button>
        
        <div className="progress-bar-container">
          <div 
            className="progress-bar"
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const pos = (e.clientX - rect.left) / rect.width;
              seek(pos * duration);
            }}
          >
            <div 
              className="progress-fill"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <div className="time-display">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>
        
        <select 
          value={playbackRate} 
          onChange={(e) => changePlaybackRate(parseFloat(e.target.value))}
          aria-label="Playback rate"
        >
          <option value="0.5">0.5x</option>
          <option value="0.75">0.75x</option>
          <option value="1.0">1.0x</option>
          <option value="1.25">1.25x</option>
          <option value="1.5">1.5x</option>
          <option value="2.0">2.0x</option>
        </select>
      </div>
      
      {transcript && (
        <div className="transcript-container">
          <button 
            className="toggle-transcript" 
            onClick={() => setShowTranscript(!showTranscript)}
          >
            {showTranscript ? 'Hide Transcript' : 'Show Transcript'}
          </button>
          
          {showTranscript && (
            <div className="transcript-text">
              {transcript}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### 3. Application Entry Points

#### 3.1 Backend Main

```python
# podcast_digest_agent/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from podcast_digest_agent.api.routers import audio, config, tasks, websocket
from podcast_digest_agent.config.settings import settings

# Create FastAPI application
app = FastAPI(
    title="Podcast Digest Agent API",
    description="API for processing YouTube podcasts into audio digests",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(audio.router, prefix=settings.API_V1_STR)
app.include_router(config.router, prefix=settings.API_V1_STR)
app.include_router(tasks.router, prefix=settings.API_V1_STR)
app.include_router(websocket.router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run(
        "podcast_digest_agent.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
```

#### 3.2 Frontend Layout

```tsx
// src/app/layout.tsx
import { Providers } from '@/providers/providers';
import { Header } from '@/components/common/layout/header';
import { Footer } from '@/components/common/layout/footer';
import '@/styles/globals.css';

export const metadata = {
  title: 'Podcast Digest Agent',
  description: 'Create audio digests from YouTube podcasts',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="min-h-screen flex flex-col">
            <Header />
            <main className="flex-grow">
              {children}
            </main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}
```

```tsx
// src/providers/providers.tsx
import { ThemeProvider } from '@/components/common/layout/theme-provider';
import { QueryProvider } from '@/components/common/layout/query-provider';
import { WorkflowProvider } from '@/contexts/workflow-context';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider defaultTheme="system" storageKey="theme">
      <QueryProvider>
        <WorkflowProvider>
          {children}
        </WorkflowProvider>
      </QueryProvider>
    </ThemeProvider>
  );
}
```

## Migration Strategy

### 1. Incremental Migration Approach

To minimize disruption while restructuring, follow these steps:

1. **Create New Structure**:
   - Set up the new directory structure
   - Create empty files for new components

2. **Move Code in Phases**:
   - Start with one component at a time
   - Keep the old code working while migrating
   - Update imports as you go

3. **Migration Phases**:
   
   **Phase 1: Core Domain Models**
   - Create domain models
   - Move and adapt agent implementations
   - Update pipeline coordination

   **Phase 2: API Reorganization**
   - Create API schemas
   - Refactor API endpoints
   - Update service implementations

   **Phase 3: Infrastructure and Utilities**
   - Move and update infrastructure components
   - Refactor utility functions
   - Implement new service interfaces

   **Phase 4: Frontend Reorganization**
   - Set up new component structure
   - Implement API integrations
   - Create custom hooks
   - Update contexts

### 2. Testing During Migration

Maintain comprehensive tests during migration:

1. Keep existing tests running
2. Add new tests for reorganized components
3. Use integration tests to verify overall functionality
4. Ensure test coverage doesn't decrease

### 3. Documentation Updates

Update documentation to reflect the new structure:

1. Create architecture diagrams
2. Document new patterns and conventions
3. Update API documentation
4. Create migration guides for developers

## Implementation Plan

### Phase 1: Preparation and Planning

1. **Create Directory Structure**:
   - Set up new directory hierarchy
   - Create placeholder files
   - Update imports in existing files

2. **Update Build Configuration**:
   - Adjust package configuration
   - Update import paths
   - Ensure tests can run with new structure

### Phase 2: Backend Restructuring

1. **Domain Models**:
   - Create core domain models
   - Define agent interfaces
   - Implement pipeline interfaces

2. **Domain Implementations**:
   - Move agent implementations
   - Refactor tool implementations
   - Update service implementations

3. **API Layer**:
   - Create API schemas
   - Refactor API endpoints
   - Update API dependencies

### Phase 3: Frontend Restructuring

1. **Component Reorganization**:
   - Create domain-based component structure
   - Move and refactor existing components
   - Update component props and interfaces

2. **API Integration**:
   - Create API client
   - Implement WebSocket manager
   - Define API types

3. **State Management**:
   - Refactor context providers
   - Create custom hooks
   - Update application state flow

### Phase 4: Testing and Validation

1. **Run Tests**:
   - Update test imports
   - Run existing tests
   - Fix failing tests

2. **Manual Testing**:
   - Test end-to-end functionality
   - Verify API integration
   - Test WebSocket functionality

### Phase 5: Documentation and Cleanup

1. **Update Documentation**:
   - Document new architecture
   - Create component guides
   - Update API documentation

2. **Clean Up**:
   - Remove old files
   - Fix lint issues
   - Update README

## Considerations and Constraints

1. **Backward Compatibility**:
   - Maintain API compatibility during restructuring
   - Ensure existing clients continue to work

2. **Testing Impact**:
   - Update test imports and fixtures
   - Ensure test coverage doesn't decrease

3. **Performance Considerations**:
   - Monitor performance during restructuring
   - Optimize API calls and data flow

4. **Documentation**:
   - Keep documentation in sync with changes
   - Document new patterns and conventions

5. **Deployment Impact**:
   - Update CI/CD pipelines for new structure
   - Ensure smooth deployment during transition

6. **Learning Curve**:
   - Provide guidance for developers on new structure
   - Document design decisions and patterns