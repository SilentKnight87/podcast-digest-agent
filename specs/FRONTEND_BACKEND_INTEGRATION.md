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