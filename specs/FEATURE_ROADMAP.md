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
    -   ✅ Hero section with URL input (URL input exists, dynamic display logic for processing/results is now functional via WorkflowContext)
    -   ✅ Layout Centering & Responsiveness: Center `ProcessTimeline` and `Footer` components and ensure they are responsive on all screen sizes.

-   ✅ Mock Data Integration: 
    -   ✅ Load and display data from `mock_data.json` in UI components (Initial data for context comes from `mock_data.json`)
    -   ✅ Create a test harness to simulate the entire processing workflow (Implemented via `WorkflowContext` and its simulation logic)
    -   ✅ Implement a mock "Start Processing" button that triggers the workflow visualization (Done in `HeroSection.tsx`)
    -   ⏳ Display processing status, agent status list, and results in appropriate components (`HeroSection` shows overall status; `ProcessingVisualizer` will show agent/flow details)
    -   [ ] Allow developers to manually trigger state changes for testing (Could be a future enhancement for dev tools)
    -   ✅ Replace the `Waveform` component (or its placeholder in `HeroSection.tsx`) with the dynamic `ProcessingVisualizer` when processing begins
    -   ✅ Implement a smooth transition from workflow visualization to audio player upon completion (`PlayDigestButton` is the first step, full player and transition pending)
    -   ✅ Test different agent states (running, completed, error) for proper visualization (Partially done through simulation; more detailed states in `ProcessingVisualizer` needed)
-    Basic Process Visualization
    -   ✅ Static process timeline for non-processing state (Effectively, `Waveform` component serves this or no visualization shown initially)

### UI Bug Fixes and Improvements
-    ✅ Hero Section Layout Fixes
    -   ✅ Review "YouTube Video" in the headline for visibility
    -   ✅ Fix Generate button visibility
    -   ✅ Fix waveform visualization rendering issues
    -   ✅ Ensure consistent text content across UI
    -   ✅ Add gradient text effect to Hero headline
-   ✅ Visual Consistency & UI Polish
    -   ✅ Use gradients and accent colors consistently
    -   ✅ Adjust component margins and padding for optimal spacing
    -   ✅ Ensure dark/light mode transitions work across all components
    -   ✅ Review all components for adherence to `specs/UI_SPECIFICATIONS.md` (colors, typography, spacing, etc.)

### Agent Workflow Visualization

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


-   ✅ Agent Workflow Data Models: 
    -   ✅ Define TypeScript interfaces for agent states and data flow based on `mock_data.json` and `UI_SPECIFICATIONS.md`.
    -   ✅ Create a context provider or state management for workflow state.
    -   ✅ Implementation includes the following key interfaces:
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

-   ✅ ProcessingVisualizer Component: 
    -   ✅ Create a new component `ProcessingVisualizer.tsx` in the Process directory
    -   ✅ This component will replace `Waveform` component inside `podcast-digest-ui/src/components/Hero/HeroSection.tsx` when processing begins
    -   ✅ Design a node-based visualization that matches the pipeline_runner.py workflow and visually looks similar to `specs/assets/visualization_inspiration.png`
    -   ✅ Each agent in the pipeline is represented as a node:
        - **YouTube Node**: Icon: `fa/FaYoutube` from react-icons - Represents the initial video source
        - **Transcript Fetcher Node**: Icon: `FileText` from Lucide - Fetches transcripts
        - **Summarizer Node**: Icon: `Brain` from Lucide - Processes transcripts into summaries
        - **Synthesizer Node**: Icon: `MessageSquare` from Lucide - Converts summaries to dialogue
        - **Audio Generator Node**: Icon: `Mic` from Lucide - Generates audio from dialogue
        - **UI/Player Node**: Icon: `PlayCircle` from Lucide - Final output for the user
    -   ✅ Once processing is complete, the visualization transitions to show a prominent play button

-   ✅ Flow Animation & Visual Effects: 
    -   ✅ Use Motion.dev for all animations
    -   ✅ Create particle flow animations between nodes to represent data transfer
    -   ✅ Implementation details:
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
    -   ✅ Use different colors for different data types:
        - Transcript data: Primary color
        - Summary data: Secondary color
        - Audio data: Accent color
    -   ✅ Add node status visualizations:
        - Pending: Muted appearance
        - Running: Pulsing animation using Framer Motion
        - Completed: Success color with checkmark
        - Error: Error color with error icon
    -   ✅ Add progress bars within each node to show completion percentage

-   ✅ Agent Interaction & Details Panel:
    -   ✅ Implement hover states to show agent descriptions
    -   ✅ Add click interaction to show detailed information panel
    -   ✅ Details panel includes:
        - Agent name and description
        - Current status and progress
        - Start/end time (if available)
        - Recent logs from the agent
        - Metrics specific to that agent (word count, confidence, etc.)
    -   ✅ Add tooltips for important status information

-   ✅ Conditional Rendering in HeroSection:
    -   ✅ The `HeroSection.tsx` component manages the display state in the area initially occupied by the `Waveform` component
    -   ✅ Initially (e.g., before URL submission or when not processing), `HeroSection.tsx` displays the `Waveform` or default content
    -   ✅ During processing, it displays the `ProcessingVisualizer`
    -   ✅ After successful completion, it displays the `PlayDigestButton` (which will later be part of the full `AudioPlayer`)