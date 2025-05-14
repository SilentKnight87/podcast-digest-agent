# Podcast Digest Agent - Feature Roadmap

This document outlines the planned features and development phases for the Podcast Digest Agent project.

## Overall Project Goal

To create a web application that allows users to input YouTube video URLs, process them to generate a summarized audio digest, and play the audio back to the user.

## Phase 1: Core Backend API & Basic API Functionality

### Backend (Python/FastAPI)
-   **[ ] API Endpoint for URL Submission:**
    -   `POST /api/v1/process_youtube_url`
    -   Accepts: YouTube URL, optional configuration (voice, summary length, audio style).
    -   Action: Triggers the backend processing pipeline (transcription, summarization, TTS).
    -   Returns: A task ID for status polling and basic video metadata.
    -   Response format:
    ```json
    {
      "taskId": "task-uuid",
      "status": "processing",
      "videoDetails": {
        "title": "Video Title",
        "thumbnail": "thumbnail_url",
        "channelName": "Channel Name",
        "duration": 1234  // in seconds
      }
    }
    ```

-   **[ ] API Endpoint for Status Polling:**
    -   `GET /api/v1/status/{task_id}`
    -   Accepts: Task ID.
    -   Returns: Detailed status information including:
      - Overall progress and status
      - Current active agent information
      - Timeline of task progress
      - Individual agent statuses and progress
      - Data flow between agents
    -   Response format should match the structure in `mock_data.json`:
    ```json
    {
      "processingStatus": {
        "overallProgress": 65,
        "status": "processing", // "processing", "completed", "failed"
        "currentAgentId": "summarizer-agent",
        "startTime": "2023-07-01T15:30:45Z",
        "estimatedEndTime": "2023-07-01T15:45:45Z",
        "elapsedTime": "00:11:30",
        "remainingTime": "00:03:30"
      },
      "agents": [
        // Array of agent objects with status, progress, logs, etc.
      ],
      "dataFlows": [
        // Array of data flow objects between agents
      ],
      "timeline": [
        // Chronological events in the processing pipeline
      ]
    }
    ```
    -   When complete, includes URL to the audio file and summary content.

-   **[ ] API Endpoint for Serving Audio:**
    -   `GET /audio/{filename.mp3}`
    -   Serves generated audio files from the `output_audio/` directory.

-   **[ ] API Endpoint for Task History:**
    -   `GET /api/v1/history`
    -   Returns: List of previously processed tasks with their summaries and audio links.
    -   Optional pagination parameters: `limit` and `offset`.
    -   Response should include an array of completed tasks similar to the `completedTasks` in `mock_data.json`.

-   **[ ] API Endpoint for Configuration Options:**
    -   `GET /api/v1/config`
    -   Returns available configuration options including:
      - Available TTS voices
      - Summary length options
      - Audio style options
    -   Format should match the `configOptions` structure in `mock_data.json`.

-   **[ ] Core Processing Logic Integration:**
    -   Integrate existing YouTube transcription.
    -   Integrate summarization agent.
    -   Integrate `audio_tools.py` for Text-to-Speech (TTS) using Google Cloud.
    -   Implement detailed agent status tracking and event logging.

-   **[ ] Asynchronous Task Handling:**
    -   Implement a robust way to handle long-running processing tasks in the background (e.g., using FastAPI's background tasks or a dedicated task queue like Celery).
    -   Ensure each agent's progress and status is tracked and can be queried.

-   **[ ] Configuration Management:**
    -   Securely manage API keys and configurations (e.g., using `.env` files and Pydantic settings).
    -   Store and retrieve user preferences for TTS voices and summary options.

-   **[ ] Basic Error Handling:**
    -   Implement error handling for common issues (invalid URLs, API failures, processing errors).
    -   Provide detailed error information in API responses.
    -   Log errors for troubleshooting.

## Phase 2: Enhanced Frontend Development (Next.js + shadcn/ui)

### Frontend Setup & Base Components
-   ✅ Next.js Project Setup
    -   ✅ Initialize Next.js 14+ app with App Router
    -   ✅ Configure TypeScript
    -   ✅ Set up Tailwind CSS
    -   ✅ Install shadcn/ui component system
    -   ✅ Configure Lucide icons
-   ✅ Design System Implementation
    -   ✅ Implement color palette, typography, and spacing system
    -   ✅ Create theme provider for dark/light mode
    -   ✅ Create base layout components (Navbar, Footer, Layout)
    -   ✅ Set up responsive breakpoints (Utilizing Tailwind CSS defaults as documented in UI_SPECIFICATIONS.md)
    -   ✅ Background Enhancement: Subtle mesh gradient for main page background using colors from `UI_SPECIFICATIONS.md`.

### Core UI Development
-    Homepage & Layout Components
    -   Navbar with theme switcher
    -   Hero section with URL input
    -   ✅ Layout Centering & Responsiveness: Center `ProcessTimeline` and `Footer` components and ensure they are responsive on all screen sizes.
    -   Section layout components
    -   Footer
-   [ ] Mock Data Integration: 
    -   Load and display data from `mock_data.json` in UI components
    -   Create a test harness to simulate the entire processing workflow
    -   Implement a mock "Start Processing" button that triggers the workflow visualization
    -   Display processing status, agent status list, and results in appropriate components
    -   Allow developers to manually trigger state changes for testing
    -   Replace the static `ProcessTimeline` with the dynamic `ProcessingVisualizer` when processing begins
    -   Implement transition from workflow visualization to audio player upon completion
    -   Test different agent states (running, completed, error) for proper visualization
-    Basic Process Visualization
    -   Static process timeline for non-processing state
-   [ ] Audio Player Implementation
    -   Build enhanced audio player with play/pause/seek controls and audio visualization
    -   Player should appear in place of the workflow visualization after processing completes
    -   Implement smooth transition animation from workflow visualization to audio player
    -   Display a prominent play button with audio waveform visualization
    -   Include player controls: play/pause, seek, volume, and playback speed
    -   Show audio duration and current position
    -   Implement audio visualization that responds to audio playback
    -   Ensure player state persists if user navigates away and returns
    -   Add accessibility features (keyboard controls, ARIA attributes)

### UI Bug Fixes and Improvements
-    Hero Section Layout Fixes
    -   Review "YouTube Video" in the headline for visibility
    -   Fix Generate button visibility
    -   Fix waveform visualization rendering issues
    -   Ensure consistent text content across UI
    -   Add gradient text effect to Hero headline
-   [ ] Visual Consistency & UI Polish
    -   Use gradients and accent colors consistently
    -   Adjust component margins and padding for optimal spacing
    -   Ensure dark/light mode transitions work across all components
    -   Review all components for adherence to `specs/UI_SPECIFICATIONS.md` (colors, typography, spacing, etc.)

### Agent Workflow Visualization
-   [ ] Agent Workflow Data Models: 
    -   Define TypeScript interfaces for agent states and data flow based on `mock_data.json` and `UI_SPECIFICATIONS.md`.
    -   Create a context provider or state management for workflow state.
    -   Implementation should include the following key interfaces:
        ```typescript
        // Agent node interface
        interface AgentNode {
          id: string;
          name: string;
          description: string;
          type: string;
          status: 'pending' | 'running' | 'completed' | 'error';
          progress: number; // 0-100
          startTime?: string;
          endTime?: string;
          icon: string; // Lucide icon name
          logs?: Array<{timestamp: string, level: string, message: string}>;
        }

        // Data flow interface
        interface DataFlow {
          id: string;
          fromAgentId: string;
          toAgentId: string;
          dataType: string;
          status: 'pending' | 'transferring' | 'completed' | 'error';
          metadata?: Record<string, any>;
        }

        // Overall processing status
        interface ProcessingStatus {
          overallProgress: number;
          status: 'processing' | 'completed' | 'failed';
          currentAgentId: string;
          startTime: string;
          estimatedEndTime?: string;
          elapsedTime: string;
          remainingTime?: string;
        }
        ```

-   [ ] ProcessingVisualizer Component: 
    -   Create a new component `ProcessingVisualizer.tsx` in the Process directory
    -   This component will replace `ProcessTimeline` when processing begins
    -   Design a node-based visualization that matches the pipeline_runner.py workflow
    -   Each agent in the pipeline should be represented as a node:
        - **YouTube Node**: Icon: `fa/FaYoutube` from react-icons - Represents the initial video source
        - **Transcript Fetcher Node**: Icon: `FileText` from Lucide - Fetches transcripts
        - **Summarizer Node**: Icon: `Brain` from Lucide - Processes transcripts into summaries
        - **Synthesizer Node**: Icon: `MessageSquare` from Lucide - Converts summaries to dialogue
        - **Audio Generator Node**: Icon: `Mic` from Lucide - Generates audio from dialogue
        - **UI/Player Node**: Icon: `PlayCircle` from Lucide - Final output for the user
    -   Implement a dark theme graph visualization with nodes connected by animated paths
    -   Once processing is complete, the visualization should transition to show a prominent play button

-   [ ] Flow Animation & Visual Effects: 
    -   Use Framer Motion for all animations
    -   Create particle flow animations between nodes to represent data transfer
    -   Implementation details:
        ```jsx
        // Example for creating animated particle flow
        <motion.div
          className="particle"
          initial={{ x: startX, y: startY, opacity: 0 }}
          animate={{ x: endX, y: endY, opacity: [0, 1, 0] }}
          transition={{ 
            duration: 1.5, 
            ease: "linear",
            repeat: Infinity,
            repeatType: "loop",
            delay: index * 0.2 // Stagger particles
          }}
        />
        ```
    -   Use different colors for different data types:
        - Transcript data: Primary color
        - Summary data: Secondary color
        - Audio data: Accent color
    -   Add node status visualizations:
        - Pending: Muted appearance
        - Running: Pulsing animation using Framer Motion
        - Completed: Success color with checkmark
        - Error: Error color with error icon
    -   Add progress bars within each node to show completion percentage

-   [ ] Agent Interaction & Details Panel:
    -   Implement hover states to show agent descriptions
    -   Add click interaction to show detailed information panel
    -   Details panel should include:
        - Agent name and description
        - Current status and progress
        - Start/end time (if available)
        - Recent logs from the agent
        - Metrics specific to that agent (word count, confidence, etc.)
    -   Add tooltips for important status information

-   [ ] ProcessTimeline Integration:
    -   Create a parent component that conditionally renders either:
        - `ProcessTimeline` (static) when not processing
        - `ProcessingVisualizer` (dynamic) when processing is active
    -   Implement a smooth transition between these two states
    -   When processing completes, transition to show the audio player component
    -   Audio player should only appear once processing is 100% complete

-   [ ] Responsive Adaptations: 
    -   Design a mobile-friendly version that stacks nodes vertically
    -   Implement tablet layout that maintains the visual flow but with adjusted spacing
    -   Use CSS Grid or Flexbox for responsive layout adjustments
    -   Ensure all interactive elements are accessible on touch devices
    -   Add appropriate ARIA attributes for accessibility

-   [ ] Mock Data Connection:
    -   Connect the visualization to the mock data from `mock_data.json`
    -   Create a simulation mode that cycles through the different agent states for testing
    -   Add mock timeline events that update at regular intervals
    -   Implement mock data transitions between states (pending → running → completed)

### WebSocket Integration
-   [ ] WebSocket Client Setup: Implement connection management, status indicators, and reconnection logic.
-   [ ] Real-time Update Handling: Process WebSocket messages and update UI state based on backend events. Handle connection errors.

### Results Display
-   [ ] Summary Display Components: Build `SummaryCard` for summary, key points, and quotes.
-   [ ] Enhanced Audio Integration: Integrate audio player with transcript, progress tracking, and playback speed controls.

### Phase 2 Advanced Frontend Features
-   [ ] User Authentication UI: Login/signup forms, profile management, and processed video history.
-   [ ] Advanced Visualization Features:
    -   Detailed data flow visualization with interactive controls
    -   Agent logs viewer with search and filtering
    -   Real-time performance metrics and analytics dashboard
-   [ ] Advanced Audio Player Controls:
    -   Playback speed, skip forward/backward
    -   Transcript synchronization
-   [ ] Additional Analytics Features:
    -   Basic usage statistics 
    -   Performance indicators

## Phase 3: Advanced Features & Scalability

### Backend Enhancements
-   **[ ] WebSocket Server Implementation:**
    -   Set up WebSocket endpoint for real-time updates
    -   Implement event emission for agent status changes
    -   Include detailed progress information
    -   Ensure message format matches the structure in `mock_data.json`
    -   Support the following event types:
      - `process_started`: Initial task creation
      - `agent_started`: When an agent begins processing
      - `progress_update`: Real-time progress updates
      - `agent_completed`: When an agent finishes
      - `data_transfer`: When data moves between agents
      - `process_completed`: When the entire task is finished
      - `error`: When something goes wrong
-   **[ ] Detailed Agent Status Tracking:**
    -   Enhanced data model for agent statuses
    -   Per-agent progress tracking
    -   Timing measurements
    -   Agent logs and metrics collection
    -   Create a unified task history database
-   **[ ] User Accounts & Authentication (Optional):**
    -   Allow users to create accounts to save their history.
-   **[ ] Database Integration:**
    -   Store task information, user data, and metadata about processed videos in a database.
    -   Schema should support all data in the mock data structure.
-   **[ ] Customizable Summarization Options:**
    -   Allow users to specify summarization length or style (if feasible).
    -   Store preferences in user profiles.
-   **[ ] Choice of Voices for TTS:**
    -   Allow users to select different voices for the audio output.
    -   Preview voice samples.
-   **[ ] Scalability Improvements:**
    -   Optimize backend for handling more concurrent requests (e.g., worker scaling, database optimizations).
    -   Consider serverless functions for parts of the pipeline.
    -   Implement caching for frequently accessed data.
-   **[ ] Logging & Monitoring:**
    -   Implement comprehensive logging and monitoring for the backend services.
    -   Track agent performance metrics.
    -   Set up alerts for system failures.

### Advanced/Optional Frontend Features
-   **[ ] User Authentication UI:**
    -   Login/signup forms
    -   Profile management
    -   History of processed videos
-   **[ ] Advanced Visualization Features:**
    -   Detailed data flow visualization with interactive controls
    -   Agent logs viewer with search and filtering
    -   Real-time performance metrics and analytics dashboard
    -   Process analytics with historical comparisons
    -   Save and replay processing history
    -   Custom visualization themes and layouts
-   **[ ] Advanced Audio Player Controls:**
    -   Playback speed, skip forward/backward
    -   Transcript synchronization
    -   Highlight current section being played
-   **[ ] Display Transcript Snippets:**
    -   Show parts of the transcript alongside the summary
    -   Searchable transcript 
-   **[ ] Shareable Links to Summaries:**
    -   Generate unique links for users to share their audio summaries
-   **[ ] Offline Support:**
    -   PWA capabilities
    -   Local storage for history
    -   Service workers for caching
-   **[ ] Additional Analytics Features:**
    -   Usage statistics and trends
    -   Performance monitoring
    -   User behavior insights

## Future Ideas & Considerations

-   **[ ] Support for Other Platforms (e.g., Vimeo, direct audio uploads).**
-   **[ ] Multi-language Support for Transcription and TTS.**
-   **[ ] Batch Processing of Multiple URLs.**
-   **[ ] Admin Dashboard for monitoring system health and usage.**
-   **[ ] Email Notifications upon completion for very long tasks.**
-   **[ ] More sophisticated summarization models or techniques.**
-   **[ ] Caching of frequently requested summaries/audio.**
-   **[ ] Mobile App (React Native) for native mobile experience.**
-   **[ ] API access for third-party integrations.**
-   **[ ] Custom branding options for enterprise users.**
-   **[ ] AI Voice Welcome: Implement an optional AI voice overlay on page open for new users with a welcoming message (e.g., "Welcome to PodcastDigest! Ready to transform long videos into quick audio summaries and save hours?"). This could be configurable by the user.**
