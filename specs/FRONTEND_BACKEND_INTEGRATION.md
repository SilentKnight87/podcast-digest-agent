# Frontend-Backend Integration Specification

## Overview

This specification outlines the implementation plan for connecting the Next.js frontend with the FastAPI backend of the Podcast Digest Agent. Currently, the frontend operates with mock data, while the backend has a functional API that isn't being utilized by the frontend.

## Goals

1. Create a seamless integration between frontend and backend
2. Implement real-time updates via WebSockets
3. Replace mock data with actual API calls
4. Ensure type safety between frontend and backend interfaces
5. Implement proper error handling and loading states

## Implementation Details

### 1. API Client Implementation

Create a dedicated API client in the frontend:

```typescript
// podcast-digest-ui/src/lib/api-client.ts

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API endpoints
export const api = {
  // Configuration
  getConfig: () => apiClient.get('/config'),
  
  // Processing
  processYoutubeUrl: (youtubeUrl: string) => 
    apiClient.post('/process_youtube_url', { youtube_url: youtubeUrl }),
  
  // Status
  getTaskStatus: (taskId: string) => 
    apiClient.get(`/status/${taskId}`),
  
  // History
  getTaskHistory: (limit = 10, offset = 0) => 
    apiClient.get(`/history?limit=${limit}&offset=${offset}`),
  
  // Audio
  getAudioFile: (fileName: string) => 
    `${API_BASE_URL}/api/v1/audio/${fileName}`,
};
```

### 2. WebSocket Connection Manager

Implement a WebSocket connection manager for real-time updates:

```typescript
// podcast-digest-ui/src/lib/websocket-manager.ts

import { TaskStatusResponse } from '@/types';

type WebSocketCallback = (data: TaskStatusResponse) => void;

export class WebSocketManager {
  private socket: WebSocket | null = null;
  private callbacks: WebSocketCallback[] = [];
  private taskId: string | null = null;
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  connect(taskId: string): void {
    this.taskId = taskId;
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${wsProtocol}://${this.apiBaseUrl.replace(/^https?:\/\//, '')}/api/v1/ws/status/${taskId}`;
    
    this.socket = new WebSocket(wsUrl);
    
    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskStatusResponse;
        this.callbacks.forEach(callback => callback(data));
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    this.socket.onclose = () => {
      console.log('WebSocket connection closed');
      // Implement reconnection logic if needed
    };
    
    this.socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.taskId = null;
  }

  subscribe(callback: WebSocketCallback): () => void {
    this.callbacks.push(callback);
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

export const websocketManager = new WebSocketManager();
```

### 3. Environment Variables Configuration

Create `.env.local` and `.env.production` files:

```
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```
# .env.production
NEXT_PUBLIC_API_URL=/api
```

Update `next.config.ts` for production:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*', // Docker service name
      },
    ];
  },
};

export default nextConfig;
```

### 4. Updating WorkflowContext

Replace mock data with real API integration:

```typescript
// podcast-digest-ui/src/contexts/WorkflowContext.tsx
import { api } from '@/lib/api-client';
import { websocketManager } from '@/lib/websocket-manager';

// Within WorkflowProvider:
function startProcessing(youtubeUrl: string) {
  setIsProcessing(true);
  setSelectedAgent(null);
  
  api.processYoutubeUrl(youtubeUrl)
    .then(response => {
      const { task_id } = response.data;
      
      // Connect WebSocket for real-time updates
      websocketManager.connect(task_id);
      
      // Subscribe to updates
      const unsubscribe = websocketManager.subscribe((data) => {
        setWorkflowState(prevState => ({
          ...prevState,
          ...data,
        }));
        
        if (data.processing_status.status === 'completed' || 
            data.processing_status.status === 'failed') {
          setIsProcessing(false);
          websocketManager.disconnect();
        }
      });
      
      // Initial task status
      api.getTaskStatus(task_id)
        .then(statusResponse => {
          setWorkflowState(statusResponse.data);
        })
        .catch(error => {
          console.error('Error fetching initial task status:', error);
          setIsProcessing(false);
        });
      
      return () => unsubscribe();
    })
    .catch(error => {
      console.error('Error starting processing:', error);
      setIsProcessing(false);
      // Handle error state
    });
}
```

### 5. Type Safety Between Frontend and Backend

Create shared types that match the Pydantic models:

```typescript
// podcast-digest-ui/src/types/api-types.ts

export interface ProcessUrlRequest {
  youtube_url: string;
}

export interface ProcessUrlResponse {
  task_id: string;
  status: string;
}

export interface TaskStatusResponse {
  task_id: string;
  processing_status: {
    status: 'queued' | 'processing' | 'completed' | 'failed';
    overall_progress: number;
    current_agent_id: string | null;
    start_time?: string;
    end_time?: string;
  };
  agents: Array<{
    id: string;
    name: string;
    status: 'pending' | 'running' | 'completed' | 'error';
    progress: number;
    start_time?: string;
    end_time?: string;
  }>;
  summary_text?: string;
  audio_url?: string;
  video_details?: {
    title: string;
    thumbnail: string;
    channel_name: string;
    duration: number;
    upload_date: string;
    url: string;
  };
}

// Add additional types to match the backend models
```

### 6. Error Handling and Loading States

Implement consistent error handling in components:

```tsx
// podcast-digest-ui/src/components/Hero/HeroSection.tsx

import { useState } from 'react';
import { useWorkflowContext } from '@/contexts/WorkflowContext';

export function HeroSection() {
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { startProcessing, isProcessing } = useWorkflowContext();
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    if (!url) {
      setError('Please enter a YouTube URL');
      return;
    }
    
    if (!url.includes('youtube.com/') && !url.includes('youtu.be/')) {
      setError('Please enter a valid YouTube URL');
      return;
    }
    
    startProcessing(url);
  };
  
  return (
    <div>
      <form onSubmit={handleSubmit}>
        {/* Form fields */}
        {error && <div className="error-message">{error}</div>}
        <button type="submit" disabled={isProcessing}>
          {isProcessing ? 'Processing...' : 'Create Digest'}
        </button>
      </form>
    </div>
  );
}
```

## Testing Strategy

1. Unit Tests:
   - Test API client methods with mocked axios responses
   - Test WebSocket manager with mocked WebSocket
   - Test WorkflowContext with mocked API responses

2. Integration Tests:
   - Test the full flow of submitting a URL and receiving updates
   - Test error handling and fallback behavior
   - Test reconnection logic for WebSockets

3. End-to-End Tests:
   - Test the entire application with a running backend
   - Verify real-time updates work correctly
   - Test error scenarios and boundary conditions

## Implementation Plan

1. **Phase 1: API Client and Type Safety**
   - Create API client
   - Define shared types
   - Update environment configuration

2. **Phase 2: WebSocket Integration**
   - Implement WebSocket manager
   - Add real-time updates to WorkflowContext
   - Test basic connectivity

3. **Phase 3: UI Integration**
   - Update HeroSection component
   - Implement error handling
   - Add loading states

4. **Phase 4: Testing and Refinement**
   - Write unit and integration tests
   - Fix any issues discovered
   - Optimize performance

## Considerations and Constraints

1. **Cross-Origin Resource Sharing (CORS)**:
   - Backend needs to allow requests from frontend origin

2. **Authentication**:
   - For future implementation, consider JWT or session-based authentication

3. **Performance**:
   - WebSocket connections should be cleaned up when not in use
   - Consider debouncing API requests for high-volume operations

4. **Error Recovery**:
   - Implement reconnection logic for WebSockets
   - Handle intermittent network failures gracefully

## AI Processing Implementation

Currently, the application provides a functional UI and pipeline framework, but the actual AI processing is simulated with test data and placeholder audio files. To make this application fully functional, the following implementations are required:

### 1. Transcript Fetching from YouTube

Replace the simulated transcript fetching with actual YouTube data:

```python
# src/agents/transcript_fetcher.py

from youtube_transcript_api import YouTubeTranscriptApi
import re

class TranscriptFetcher:
    def fetch_transcript(self, youtube_url: str) -> str:
        # Extract video ID from URL
        video_id = self._extract_video_id(youtube_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {youtube_url}")
            
        # Fetch transcript using the YouTube Transcript API
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine all transcript entries into a single text
        full_transcript = " ".join([entry["text"] for entry in transcript_list])
        
        return full_transcript
        
    def _extract_video_id(self, youtube_url: str) -> str:
        # Extract video ID from various YouTube URL formats
        patterns = [
            r"youtu\.be\/([^\/\?]+)",  # youtu.be/xxxx
            r"youtube\.com\/watch\?v=([^&]+)",  # youtube.com/watch?v=xxxx
            r"youtube\.com\/embed\/([^\/\?]+)",  # youtube.com/embed/xxxx
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
                
        return None
```

### 2. Summary Generation

Implement actual summarization using LLMs instead of placeholder text:

```python
# src/agents/summarizer.py

from langchain.llms import OpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

class SummarizerAgent:
    def __init__(self, api_key: str):
        self.llm = OpenAI(temperature=0, api_key=api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200
        )
        
    def summarize(self, transcript: str) -> str:
        # Split text into manageable chunks
        docs = [Document(page_content=transcript)]
        split_docs = self.text_splitter.split_documents(docs)
        
        # Use LangChain's summarization chain
        chain = load_summarize_chain(
            self.llm, 
            chain_type="map_reduce",
            verbose=True
        )
        
        # Generate summary
        summary = chain.run(split_docs)
        return summary
```

### 3. Conversational Script Generation

Transform the summary into a conversational format for better audio digests:

```python
# src/agents/synthesizer.py

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

class SynthesizerAgent:
    def __init__(self, api_key: str):
        self.llm = OpenAI(temperature=0.7, api_key=api_key)
        
    def synthesize_conversation(self, summary: str, podcast_title: str) -> str:
        prompt_template = """
        Convert the following podcast summary into a conversational dialogue between two hosts named Alex and Jamie.
        Make it sound natural and engaging, with a brief introduction and conclusion.
        
        Podcast Title: {title}
        
        Summary:
        {summary}
        
        Conversational Script:
        """
        
        prompt = PromptTemplate(
            input_variables=["title", "summary"],
            template=prompt_template
        )
        
        formatted_prompt = prompt.format(title=podcast_title, summary=summary)
        conversational_script = self.llm(formatted_prompt)
        
        return conversational_script
```

### 4. Text-to-Speech Audio Generation

Replace test audio with actual TTS-generated content:

```python
# src/agents/audio_generator.py

from google.cloud import texttospeech
import os
import re

class AudioGenerator:
    def __init__(self, credentials_path: str = None):
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            
        self.client = texttospeech.TextToSpeechClient()
        
    def generate_audio(self, script: str, output_path: str) -> str:
        # Split script by speaker for multi-voice rendering
        parts = self._split_by_speaker(script)
        
        # Generate audio for each part and combine
        audio_contents = []
        
        for speaker, text in parts:
            voice_params = self._get_voice_params(speaker)
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(**voice_params)
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            audio_contents.append(response.audio_content)
            
        # Combine audio using ffmpeg or another audio processing library
        # For simplicity, this example just saves the first part
        with open(output_path, "wb") as out:
            for content in audio_contents:
                out.write(content)
                
        return output_path
        
    def _split_by_speaker(self, script: str):
        # Simple regex to split by "Alex:" and "Jamie:" patterns
        pattern = r"(Alex|Jamie):\s*(.*?)(?=(?:Alex|Jamie):|$)"
        matches = re.findall(pattern, script, re.DOTALL)
        return [(speaker, text.strip()) for speaker, text in matches]
        
    def _get_voice_params(self, speaker: str):
        # Different voices for different speakers
        if speaker.lower() == "alex":
            return {
                "language_code": "en-US",
                "name": "en-US-Neural2-D",
                "ssml_gender": texttospeech.SsmlVoiceGender.MALE
            }
        else:
            return {
                "language_code": "en-US",
                "name": "en-US-Neural2-F",
                "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
            }
```

### 5. Pipeline Integration

Update the pipeline to use the actual agents instead of placeholders:

```python
# src/processing/pipeline.py

import logging
import os
from pathlib import Path
from typing import Dict, Any

from src.agents.transcript_fetcher import TranscriptFetcher
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.audio_generator import AudioGenerator
from src.config.settings import settings

logger = logging.getLogger(__name__)

class PipelineProcessor:
    def __init__(self):
        # Initialize agents with proper credentials
        openai_api_key = os.getenv("OPENAI_API_KEY")
        google_credentials = settings.google_credentials_path
        
        self.transcript_fetcher = TranscriptFetcher()
        self.summarizer = SummarizerAgent(api_key=openai_api_key)
        self.synthesizer = SynthesizerAgent(api_key=openai_api_key)
        self.audio_generator = AudioGenerator(credentials_path=google_credentials)
        
    async def process(self, task_id: str, youtube_url: str, update_callback=None) -> Dict[str, Any]:
        """Process a YouTube URL through the full pipeline."""
        result = {
            "task_id": task_id,
            "youtube_url": youtube_url,
            "transcript": "",
            "summary": "",
            "script": "",
            "audio_path": "",
            "status": "processing"
        }
        
        try:
            # Step 1: Fetch transcript
            if update_callback:
                await update_callback(task_id, "transcript-fetcher", "running", 0)
                
            result["transcript"] = self.transcript_fetcher.fetch_transcript(youtube_url)
            
            if update_callback:
                await update_callback(task_id, "transcript-fetcher", "completed", 100)
                await update_callback(task_id, "summarizer", "running", 0)
            
            # Step 2: Generate summary
            result["summary"] = self.summarizer.summarize(result["transcript"])
            
            if update_callback:
                await update_callback(task_id, "summarizer", "completed", 100)
                await update_callback(task_id, "synthesizer", "running", 0)
            
            # Step 3: Create conversational script
            # Get video title (in a real implementation, you'd extract this)
            podcast_title = "YouTube Podcast"  # Placeholder
            result["script"] = self.synthesizer.synthesize_conversation(
                result["summary"],
                podcast_title
            )
            
            if update_callback:
                await update_callback(task_id, "synthesizer", "completed", 100)
                await update_callback(task_id, "audio-generator", "running", 0)
            
            # Step 4: Generate audio
            audio_dir = Path(settings.output_audio_dir)
            audio_dir.mkdir(exist_ok=True)
            
            audio_file_path = audio_dir / f"{task_id}.mp3"
            self.audio_generator.generate_audio(result["script"], str(audio_file_path))
            
            result["audio_path"] = str(audio_file_path)
            result["status"] = "completed"
            
            if update_callback:
                await update_callback(task_id, "audio-generator", "completed", 100)
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline processing error: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)
            
            if update_callback:
                # Update the current agent status to error
                current_agent = "unknown"
                if "transcript" not in result or not result["transcript"]:
                    current_agent = "transcript-fetcher"
                elif "summary" not in result or not result["summary"]:
                    current_agent = "summarizer"
                elif "script" not in result or not result["script"]:
                    current_agent = "synthesizer"
                elif "audio_path" not in result or not result["audio_path"]:
                    current_agent = "audio-generator"
                    
                await update_callback(task_id, current_agent, "error", 0)
                
            return result
```

### 6. Frontend Integration Adjustments

Update the frontend to handle the new data format and features:

```typescript
// podcast-digest-ui/src/components/Hero/PlayDigestButton.tsx

// Inside the component:
const handlePlayClick = () => {
  if (workflowState?.audio_url) {
    // Get the audio URL
    const audioUrl = api.getAudioFile(workflowState.audio_url);
    
    // Set the source and play
    if (audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.load();
      audioRef.current.play()
        .then(() => {
          setIsPlaying(true);
        })
        .catch(error => {
          console.error('Error playing audio:', error);
          // Handle error state or show fallback
        });
    }
  }
};
```

### 7. Required Dependencies

Update the project dependencies:

```
# requirements.txt additions
youtube-transcript-api>=0.5.0
langchain>=0.0.167
openai>=0.27.0
google-cloud-texttospeech>=2.14.1
ffmpeg-python>=0.2.0
```

### 8. Environment Configuration

Add the necessary environment variables:

```
# .env file
OPENAI_API_KEY=your_openai_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_google_cloud_credentials.json
```