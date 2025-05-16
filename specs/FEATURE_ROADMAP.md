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

-   **[ ] WebSocket Endpoint for Real-Time Status Updates:**
    -   `WS /api/v1/ws/status/{task_id}`
    -   **Purpose:** Provide real-time, bi-directional communication between the frontend and backend for status updates of a specific processing task. This avoids the need for constant polling by the client.
    -   **Workflow:**
        1.  Client initiates processing via `POST /api/v1/process_youtube_url` and receives a `task_id`.
        2.  Client establishes a WebSocket connection to `WS /api/v1/ws/status/{task_id}`.
        3.  As the backend pipeline (agents, data flows) progresses for that `task_id`, the backend pushes `TaskStatusResponse` messages (or a compatible, streamlined version) over the WebSocket to the connected client.
        4.  The frontend listens for these messages and updates the UI (e.g., `ProcessingVisualizer`) in real-time.
        5.  The connection is maintained until the task is completed/failed, or the client disconnects.
    -   **Message Format:** The messages sent from the server to the client should ideally conform to the `TaskStatusResponse` Pydantic model (defined in `src/models/api_models.py`) to ensure consistency with the polling endpoint.
    -   **Implementation Details for Junior Developer:**
        -   **FastAPI WebSocket Support:**
            -   Use FastAPI's `WebSocket` and `WebSocketDisconnect` for handling WebSocket connections.
            -   The endpoint function will accept `websocket: WebSocket` and `task_id: str` as parameters.
            -   Refer to [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/).
        -   **Connection Management:**
            -   Implement a connection manager (e.g., a Python class or a dictionary-based structure, potentially in `src/core/connection_manager.py` or alongside `task_manager.py`).
            -   This manager will keep track of active WebSocket connections, mapping `task_id` to one or more connected `WebSocket` objects (a list, in case multiple clients want to observe the same task).
            -   `on_connect(websocket: WebSocket, task_id: str)`: Add the WebSocket to the list of connections for the given `task_id`. Send the current status of the task immediately upon connection if available.
            -   `on_disconnect(websocket: WebSocket, task_id: str)`: Remove the WebSocket from the list for that `task_id`.
        -   **Broadcasting Updates:**
            -   Modify the existing `src/core/task_manager.py` functions (e.g., `update_task_processing_status`, `update_agent_status`, `add_timeline_event`, `set_task_completed`, `set_task_failed`).
            -   After any state change, these functions should notify the connection manager to broadcast the updated `TaskStatusResponse` to all relevant WebSocket clients subscribed to that `task_id`.
            -   The broadcast function in the connection manager will iterate through the list of WebSockets for a given `task_id` and use `await websocket.send_json(updated_status_data)` for each.
        -   **Error Handling:**
            -   Implement try-except blocks around WebSocket send/receive operations to handle potential `WebSocketDisconnect` exceptions gracefully.
            -   Log WebSocket connection errors and lifecycle events.
        -   **Initial Status Push:**
            -   When a client connects via WebSocket, immediately push the current latest status for that `task_id` (if it exists in `_tasks_store`) to the client. This ensures the client UI is up-to-date right after connection.
        -   **Testing:**
            -   Use a WebSocket client tool (e.g., Postman, or a simple Python/JavaScript client script) to test the connection, message sending, and real-time updates.

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

-   **[ ] Backend Testing Strategy:**
    -   **Objective:** Ensure all backend components (API endpoints, WebSocket, core logic) are robust, reliable, and function as expected. Adhere to the project rule: "Always create test for new features...".
    -   **Tools:**
        -   Pytest for test organization and execution.
        -   FastAPI's `TestClient` for testing HTTP API endpoints.
        -   A suitable WebSocket test client for FastAPI (e.g., `TestClient`'s WebSocket support, or `websockets` library for more direct client testing).
        -   `unittest.mock` (or `pytest-mock`) for mocking dependencies.
    -   **Unit Tests (Pytest):**
        -   **`src/config/settings.py`:**
            -   Verify correct loading of settings from environment variables.
            -   Test default values are applied when environment variables are not set.
            -   Test correct creation of `OUTPUT_AUDIO_DIR` and `INPUT_DIR`.
        -   **`src/models/api_models.py`:**
            -   Test Pydantic model validation for all request and response models.
            -   Example: `ProcessUrlRequest` should validate `youtube_url` as `HttpUrl`.
            -   Example: `AgentNode.progress` should be within 0-100.
        -   **`src/core/task_manager.py`:**
            -   Test `add_new_task()`: Correct `task_id` generation, initial status creation (including all agents and data flows as defined), and storage.
            -   Test `get_task_status()`: Retrieval of correct task data, handling of non-existent `task_id`.
            -   Test all update functions (`update_task_processing_status`, `update_agent_status`, `update_data_flow_status`, `add_agent_log`, `add_timeline_event`): Verify that the in-memory `_tasks_store` is updated correctly.
            -   Test `set_task_completed()` and `set_task_failed()`: Correct final status, inclusion of results/error messages.
        -   **`src/core/connection_manager.py` (once created for WebSockets):**
            -   Test `on_connect()`: WebSocket is added to the correct `task_id` group.
            -   Test `on_disconnect()`: WebSocket is removed.
            -   Test `broadcast()` (or similar): Messages are correctly prepared for sending (actual sending will be part of integration tests).
        -   **Individual Agent Logic (as they are developed beyond stubs):**
            -   Each agent (`TranscriptFetcher`, `SummarizerAgent`, etc.) should have unit tests for its core data processing logic, mocking external dependencies (like API calls to YouTube or LLMs).

-   **[ ] Backend Testing Strategy (Test-Driven Development - TDD):**
    -   **Core Philosophy:** Employ a Test-Driven Development (TDD) approach for all backend functionality. Tests will be written *before* the implementation code to define and verify expected behavior.
    -   **TDD Cycle:**
        1.  **Define Requirement:** Clearly define a new feature, unit of functionality, or specific behavior for an API endpoint or core logic component.
        2.  **Write Test(s) (Red):** Create one or more automated tests (unit or integration) that specify the desired functionality. These tests should initially fail because the code has not yet been implemented.
        3.  **Implement Code (Green):** Write the minimum amount of production code necessary to make the failing test(s) pass.
        4.  **Refactor (Blue/Green):** Improve the structure and quality of the implemented code (e.g., for clarity, performance, maintainability) while ensuring all tests continue to pass.
        5.  **Repeat:** Continue this cycle for all subsequent features and improvements.
    -   **Objective:** To ensure that all expected backend functionality, as outlined in this roadmap, is covered by tests *before or during its development*. This leads to a robust, well-documented, and maintainable codebase. High test coverage is a natural outcome of this process.
    -   **Tools:**
        -   **Pytest:** For test organization, execution, and fixtures.
        -   **FastAPI's `TestClient`:** For testing HTTP API endpoints.
        -   **FastAPI's WebSocket Testing Capabilities (via `TestClient`):** For testing WebSocket endpoints and real-time communication.
        -   **`unittest.mock` (or `pytest-mock`):** For mocking external dependencies and isolating units of code.
    -   **Test Granularity & Focus (Examples):**
        -   **Configuration (`src/config/settings.py`):**
            -   Tests verify correct loading of settings from environment variables and `.env` files.
            -   Tests confirm default values are applied when specific settings are not provided.
            -   Tests ensure correct resolution and creation of necessary directories (e.g., `OUTPUT_AUDIO_DIR`, `INPUT_DIR`).
        -   **API Models (`src/models/api_models.py`):**
            -   For each Pydantic model, tests assert validation rules (e.g., `ProcessUrlRequest` must have a valid `youtube_url`, `AgentNode.progress` must be between 0-100).
        -   **Core Logic (`src/core/task_manager.py`, `src/core/connection_manager.py`):**
            -   **Task Manager:** Tests for `add_new_task` will define the expected initial state of a task (agents, flows, timeline). Tests for update functions will verify correct state transitions and data storage.
            -   **Connection Manager:** Tests for `connect` and `disconnect` will ensure proper WebSocket session management. Tests for `broadcast_to_task` will verify that the correct data is prepared for sending to relevant clients.
        -   **API Endpoints (`src/main.py` - HTTP & WebSocket):**
            -   For each endpoint, tests define expected request formats, response codes, and response payloads for both success and error scenarios (e.g., valid/invalid input, resource found/not found).
            -   WebSocket tests cover connection lifecycle, initial status push, real-time message reception based on backend events, and behavior with multiple clients.
        -   **Individual Agents (e.g., `TranscriptFetcher`, `SummarizerAgent`):**
            -   Before implementing an agent's processing logic, tests are written to define its expected input, output, and interactions with external services (which will be mocked).
        -   **Background Processing Pipeline (`run_processing_pipeline`):**
            -   Tests will define the expected sequence of agent invocations, status updates via `task_manager`, and final task outcomes (success or failure) based on simulated agent behaviors.
    -   **Benefits of this TDD Approach:**
        -   **Clear Requirements:** Writing tests first forces clear definition of what the code should do.
        -   **Continuous Feedback:** Rapid feedback on whether new code meets requirements.
        -   **Design Quality:** Encourages modular and testable design.
        -   **Living Documentation:** Tests serve as executable specifications of the system.
        -   **Refactoring Confidence:** A comprehensive test suite allows for safer code refactoring and improvements.
    -   **Process for Junior Developer:**
        1.  Pick a small, well-defined feature or behavior from this roadmap (e.g., a specific field in an API response, a particular agent state update).
        2.  Write a Pytest test function in the relevant test file (e.g., `tests/api/test_main_http_api.py` or `tests/core/test_task_manager.py`) that asserts the desired outcome. Run it to see it fail.
        3.  Implement the corresponding logic in the `src` directory.
        4.  Run the test again until it passes.
        5.  Look for opportunities to clean up the code.
        6.  Commit both the test and the implementation code.

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