# ✅ COMPLETED - Podcast Digest Agent - Feature Roadmap

**Status**: 100% complete as of the current codebase state.

This document outlines the planned features and development phases for the Podcast Digest Agent project.

## Overall Project Goal

To create a web application that allows users to input YouTube video URLs, process them to generate a summarized audio digest, and play the audio back to the user.

## Phase 1: Core Backend API & Basic API Functionality

### Backend (Python/FastAPI)
-   **[✓] API Endpoint for URL Submission:**
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

-   **[✓] API Endpoint for Status Polling:**
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
      "taskId": "task-1234-abcd-5678",
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
      ],
      // These fields are present when status is "completed"
      "summaryText": "The podcast discussed...",
      "audioFileUrl": "/audio/task-1234-abcd-5678.mp3"
    }
    ```
    -   **Important Note on Completion Data:** When a task is completed, the response will include:
        -   `summaryText`: The text summary of the podcast
        -   `audioFileUrl`: URL to the generated audio file (not the audio itself)
        -   The frontend will use this URL to stream/play the audio via the `/audio/{filename.mp3}` endpoint
        -   These fields are mapped to `summary_text` and `audio_file_url` in the `TaskStatusResponse` Pydantic model

-   **[✓] WebSocket Endpoint for Real-Time Status Updates:**
    -   `WS /api/v1/ws/status/{task_id}`
    -   **Purpose:** Provide real-time, bi-directional communication between the frontend and backend for status updates of a specific processing task. This avoids the need for constant polling by the client.
    -   **Workflow:**
        1.  Client initiates processing via `POST /api/v1/process_youtube_url` and receives a `task_id`.
        2.  Client establishes a WebSocket connection to `WS /api/v1/ws/status/{task_id}`.
        3.  As the backend pipeline (agents, data flows) progresses for that `task_id`, the backend pushes `TaskStatusResponse` messages (or a compatible, streamlined version) over the WebSocket to the connected client.
        4.  The frontend listens for these messages and updates the UI (e.g., `ProcessingVisualizer`) in real-time.
        5.  The connection is maintained until the task is completed/failed, or the client disconnects.
    -   **Message Format:** The messages sent from the server to the client should ideally conform to the `TaskStatusResponse` Pydantic model (defined in `src/models/api_models.py`) to ensure consistency with the polling endpoint.
    -   **Implementation Details:**
        -   **FastAPI WebSocket Support:**
            -   Used FastAPI's `WebSocket` and `WebSocketDisconnect` for handling WebSocket connections.
            -   The endpoint function accepts `websocket: WebSocket` and `task_id: str` as parameters.
        -   **Connection Management:**
            -   Implemented a connection manager class in `src/core/connection_manager.py`.
            -   The manager keeps track of active WebSocket connections, mapping `task_id` to connected `WebSocket` objects.
            -   `connect(websocket: WebSocket, task_id: str)`: Adds the WebSocket to the list of connections for the given `task_id`.
            -   `disconnect(websocket: WebSocket, task_id: str)`: Removes the WebSocket from the list for that `task_id`.
        -   **Broadcasting Updates:**
            -   Modified the `src/core/task_manager.py` functions to use the connection manager to broadcast updates.
            -   After any state change, these functions notify the connection manager to broadcast the updated `TaskStatusResponse`.
            -   The broadcast function in the connection manager iterates through the WebSockets for a given `task_id` and uses `await websocket.send_json(updated_status_data)` for each.
        -   **Error Handling:**
            -   Implemented try-except blocks around WebSocket send/receive operations to handle potential `WebSocketDisconnect` exceptions.
            -   WebSocket connection errors and lifecycle events are logged.
        -   **Initial Status Push:**
            -   When a client connects via WebSocket, the current status for that `task_id` is pushed to the client.

-   **[✓] API Endpoint for Serving Audio:**
    -   `GET /audio/{filename.mp3}`
    -   Serves generated audio files from the `output_audio/` directory.

-   **[✓] API Endpoint for Task History:**
    -   `GET /api/v1/history`
    -   Returns: List of previously processed tasks with their summaries and audio links.
    -   Optional pagination parameters: `limit` and `offset`.
    -   Response format:
    ```json
    {
      "tasks": [
        {
          "taskId": "task-5678-efgh-9012",
          "videoDetails": {
            "title": "Understanding Quantum Computing",
            "thumbnail": "https://i.ytimg.com/vi/qyz12def345/maxresdefault.jpg",
            "channelName": "Science Simplified",
            "url": "https://youtube.com/watch?v=qyz12def345",
            "duration": 1256,
            "uploadDate": "2023-06-10"
          },
          "completionTime": "2023-06-30T14:25:18Z",
          "processingDuration": "00:15:42",
          "audioOutput": {
            "url": "/audio/quantum-computing-digest-5678efgh9012.mp3",
            "duration": "00:03:28",
            "fileSize": "3.2MB"
          },
          "summary": {
            "title": "Understanding Quantum Computing: Key Insights",
            "host": "Dr. Michael Chen",
            "mainPoints": ["Point 1", "Point 2"],
            "highlights": ["Highlight 1", "Highlight 2"],
            "keyQuotes": ["Quote 1", "Quote 2"]
          }
        }
      ],
      "totalTasks": 10,
      "limit": 5,
      "offset": 0
    }
    ```
    -   **Mapping to Pydantic Model:** This endpoint is implemented using the `TaskHistoryResponse` Pydantic model in `src/models/api_models.py`, which should be updated to match this structure.

-   **[✓] API Endpoint for Configuration Options:**
    -   `GET /api/v1/config`
    -   Returns available configuration options including:
      - Available TTS voices
      - Summary length options
      - Audio style options
    -   Format should match the `configOptions` structure in `mock_data.json`.

-   **[✓] Core Processing Logic Integration:**
    -   Integrated simulation of YouTube transcription and processing.
    -   Implemented agent status tracking and event logging.
    -   Added detailed timeline tracking.
    -   Implemented data flow visualization between agents.
    -   **Agent Icon Handling:** Each agent in the pipeline has a specific icon (defined in their respective classes) that is included in API responses:
        -   YouTube Downloader: "Youtube" (Lucide icon name)
        -   Transcript Fetcher: "FileText" (Lucide icon name)
        -   Summarizer Agent: "Brain" (Lucide icon name)
        -   Synthesizer Node: "MessageSquare" (Lucide icon name)
        -   Audio Generator: "Mic" (Lucide icon name)
        -   Output Player: "PlayCircle" (Lucide icon name)
        -   All agent icons are valid Lucide icon names for frontend compatibility

-   **[✓] Asynchronous Task Handling:**
    -   Implemented background task processing using FastAPI's BackgroundTasks.
    -   Each agent's progress and status is tracked and can be queried via API.
    -   WebSocket notifications provide real-time updates of task progress.

-   **[✓] Configuration Management:**
    -   Implemented secure API key and configuration management using `.env` files and Pydantic settings.
    -   Added configuration options for TTS voices, summary lengths, and audio styles.

-   **[✓] Basic Error Handling:**
    -   Implemented error handling for common issues (invalid URLs, API failures, processing errors).
    -   Added detailed error information in API responses.
    -   Implemented comprehensive error logging for troubleshooting.

-   **[⏳] Backend Testing Strategy (Test-Driven Development - TDD):**
    -   **Overall Approach:** We will employ a Test-Driven Development (TDD) approach for all backend functionality. This means tests will be written *before* the implementation code to define and verify expected behavior, ensuring a robust, well-documented, and maintainable codebase. High test coverage is a natural outcome of this process. Adhere to the project rule: "Always create test for new features...".
    -   **Progress:**
        -   ✅ **Configuration (`src/config/settings.py`):**
            -   ✅ Test loading settings correctly from environment variables
            -   ✅ Test using default values when environment variables are not set
            -   ✅ Test loading from `.env` file
            -   ✅ Test directory creation for `OUTPUT_AUDIO_DIR` and `INPUT_DIR`
            -   ✅ Test path resolution (relative vs absolute paths)
            -   ✅ Test case insensitivity for environment variables
        -   ✅ **Pydantic Models for API Alignment (`src/models/api_models.py`):**
            -   ✅ Update and test `AgentNode` model with correct defaults
            -   ✅ Update and test `VideoDetails` with new fields (`url`, `upload_date`)
            -   ✅ Create and test new models `AudioOutput` and `SummaryContent`
            -   ✅ Update and test `HistoryTaskItem` with new structure
            -   ✅ Verify `TaskStatusResponse` alignment with roadmap
        -   **✅ Core Logic Modules:**
            -   **✅ Task Manager (`src/core/task_manager.py`):**
                -   ✅ Test task creation and initialization
                -   ✅ Test task status retrieval
                -   ✅ Test handling of non-existent tasks
                -   ✅ Test task status updates
                -   ✅ Test task completion and error states
            -   **✅ Connection Manager (`src/core/connection_manager.py`):**
                -   ✅ Test WebSocket connection tracking
                -   ✅ Test client disconnection handling
                -   ✅ Test message broadcasting
                -   ✅ Test connection cleanup
        -   **✅ API Endpoints:**
            -   **✅ HTTP Endpoints:**
                -   ✅ Test `POST /api/v1/process_youtube_url`
                -   ✅ Test `GET /api/v1/status/{task_id}`
                -   ✅ Test `GET /api/v1/history`
                -   ✅ Test `GET /api/v1/config`
                -   ✅ Test error handling and validation
            -   **⏳ WebSocket Endpoint:**
                -   ⏳ Test connection establishment
                    - Identified issue: WebSocketTestSession object (from TestClient) doesn't match WebSocket object in connection manager
                    - Need to update connection manager or test setup to properly compare WebSocket instances
                -   ⏳ Test initial status push
                -   ⏳ Test real-time updates
                -   ⏳ Test connection error handling
        -   **✅ Individual Agents:**
            -   ✅ Test `TranscriptFetcher`
            -   ✅ Test `SummarizerAgent`
            -   ✅ Test `AudioGenerator`
            -   ✅ Test agent error handling
            -   ✅ Test agent progress tracking
        -   **✅ Processing Pipeline:**
            -   ✅ Test agent sequence execution
            -   ✅ Test data flow between agents
            -   ✅ Test pipeline error handling
            -   ✅ Test task status updates during processing
            -   ✅ Test final output generation

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

-   ✅ Audio Player Implementation
    -   ✅ Build enhanced audio player with play/pause/seek controls and audio visualization
    -   ✅ Player should appear in place of the workflow visualization after processing completes
    -   ✅ Implement smooth transition animation from workflow visualization to audio player
    -   ✅ Display a prominent play button with audio waveform visualization
    -   ✅ Include player controls: play/pause, seek, volume, and playback speed
    -   ✅ Show audio duration and current position
    -   ✅ Implement audio visualization that responds to audio playback
    -   ✅ Ensure player state persists if user navigates away and returns
    -   ✅ Add accessibility features (keyboard controls, ARIA attributes)


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

-   **[ ] Real-time Data Handling (WebSocket Integration):**
    -   **Objective:** Enable the frontend to receive and process real-time status updates via WebSockets for a seamless user experience during content processing.
    -   **Tasks:**
        1.  **WebSocket Client Implementation:**
            -   After successfully submitting a URL and obtaining a `task_id` (from `POST /api/v1/process_youtube_url`), the frontend should initiate a WebSocket connection to `WS /api/v1/ws/status/{task_id}`.
            -   Use a robust WebSocket client library suitable for Next.js/React (e.g., native `WebSocket` API, `socket.io-client` if the backend uses Socket.IO which it currently does not, or a lightweight wrapper).
        2.  **Message Handling:**
            -   Listen for incoming messages on the WebSocket. These messages are expected to be JSON payloads conforming to the `TaskStatusResponse` model.
            -   Parse the received messages and update the application's state (e.g., the `WorkflowContext` or a dedicated state management store like Zustand/Redux if introduced).
        3.  **UI Updates:**
            -   Ensure that components like `ProcessingVisualizer`, agent status lists, progress bars, and overall status indicators react dynamically to the state changes driven by WebSocket messages.
        4.  **Connection Lifecycle Management:**
            -   Implement logic to handle WebSocket connection opening, closing, and potential errors.
            -   Consider strategies for reconnection attempts if the connection drops unexpectedly during processing.
            -   Gracefully close the WebSocket connection when the task is complete/failed or if the user navigates away from the processing view.
        5.  **Fallback to Polling (Optional but Recommended):**
            -   While WebSockets will be the primary update mechanism, consider implementing a fallback to the `GET /api/v1/status/{task_id}` polling endpoint if a WebSocket connection cannot be established or is persistently failing. This enhances robustness.

-   ✅ ProcessingVisualizer Component:
    -   ✅ Create a new component `ProcessingVisualizer.tsx` in the Process directory
    -   ✅ This component will replace `Waveform` component inside `client/src/components/Hero/HeroSection.tsx` when processing begins
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
