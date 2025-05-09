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
-   [x] Next.js Project Setup:
    -   Initialize Next.js 14+ app with App Router (**Done**)
    -   Configure TypeScript (**Done**)
    -   Set up Tailwind CSS (**Done**)
    -   Install shadcn/ui component system (**Done**)
    -   Configure Lucide icons (**Done**)
-   [x] Design System Implementation:
    -   Implement color palette, typography, and spacing system (**Base Tailwind and shadcn/ui tokens in place**)
    -   Create theme provider for dark/light mode (**ThemeProvider implemented**)
    -   Create base layout components (**Navbar, Footer, Layout implemented**)
    -   Set up responsive breakpoints (**Tailwind default breakpoints in use**)
    -   **[x] Background Enhancement: Implement a subtle mesh gradient for the main page background using colors from `UI_SPECIFICATIONS.md` (e.g., Primary, Secondary, Accent) to enhance visual appeal without being distracting.**

### Core UI Development
-   [x] Homepage & Layout Components:
    -   Navbar with theme switcher (**Implemented**)
    -   Hero section with URL input (**Implemented**)
    -   Section layout components (**Base layout in place**)
    -   Footer (**Implemented**)
    -   **[ ] Layout Centering & Responsiveness: Ensure `ProcessTimeline` and `Footer` components are properly centered on the screen and dynamically adjust to various screen sizes, maintaining readability and aesthetics.**
-   [x] URL Input & Validation:
    -   Form components with validation (**Implemented in HeroSection**)
    -   Error handling and feedback (**Toasts and validation implemented**)
    -   Submit functionality (**Stubbed, ready for API integration**)
-   **[ ] Mock Data Integration:**
    -   **[ ] Implement logic to fetch and display data from `mock_data.json` to populate UI components (e.g., processing status, agent list, results) for development and testing purposes before full backend integration.**
-   [x] Basic Process Visualization:
    -   [x] Static process timeline for non-processing state (**Implemented**)
    -   Basic processing status indicators (**To be implemented**)
-   [ ] Audio Player Implementation:
    -   Enhanced audio player component (**To be implemented**)
    -   Play/pause/seek controls (**To be implemented**)
    -   Audio visualization (**To be implemented**)
    -   **[ ] Implement Play Functionality: Enable the play button on the audio player when the digest processing is complete and the audio file is available, allowing users to play the generated audio digest.**

### UI Bug Fixes and Improvements (High Priority)
-   **[x] Hero Section Layout Fixes:**
    -   [x] Review  "YouTube Video" in the headline as its currently not visable
    -   [x] Fix the Generate button visibility  (currently hard to see)
    -   [x] Fix the waveform visualization rendering issues below the input field
    -   [x] Ensure consistent text content across UI ("YouTube Video" vs "Podcast")
    -   [x] Add gradient text effect to the Hero headline for visual appeal
-   **[ ] Visual Consistency & UI Polish:**
    -   Ensure consistent use of gradients and accent colors.
    -   Review and adjust component margins and padding for optimal spacing.
    -   Ensure dark/light mode transitions work correctly across all components.
    -   **[ ] UI Specification Adherence: Conduct a thorough review of all implemented components against `specs/UI_SPECIFICATIONS.md` to ensure adherence to the defined design system (colors, typography, spacing, etc.).**

### Agent Workflow Visualization
-   [ ] Agent Workflow Data Models:
    -   Define TypeScript interfaces for agent states and data flow based on `mock_data.json` and `UI_SPECIFICATIONS.md`.
    -   Create context provider or state management solution (e.g., Zustand, Jotai, or React Query for server state) for workflow state.
-   [ ] Agent Visualization Components:
    -   ProcessTimeline component for static view (already partially implemented).
    -   ProcessingVisualizer component for displaying active processing dynamically.
    -   Progress indicators for overall and per-agent progress.
-   [ ] Flow Animation & Visual Effects:
    -   Framer Motion animations for data flow visualization between agents.
    -   Status-based styling and transitions (e.g., color changes, highlighting active agent).
    -   Interactive elements (hover states for details, click actions for logs if applicable).
    -   **[ ] Animated Workflow: Implement the animated visualization of the agent workflow. This should dynamically update as the process moves through different agents (transcription, summarization, TTS), showing data flow and progress, culminating in the final summary and audio availability.**
-   [ ] Responsive Adaptations:
    -   Mobile-friendly linear visualization for smaller screens.
    -   Tablet and desktop optimized layouts
    -   Accessibility considerations

### WebSocket Integration
-   [ ] WebSocket Client Setup:
    -   Implement WebSocket connection management
    -   Connection status indicators
    -   Reconnection logic
-   [ ] Real-time Update Handling:
    -   Process WebSocket messages
    -   Update UI state based on backend events
    -   Handle connection errors

### Results Display
-   [ ] Summary Display Components:
    -   SummaryCard layout
    -   Key points visualization
    -   Quote formatting
-   [ ] Enhanced Audio Integration:
    -   Audio player with transcript integration
    -   Progress tracking
    -   Playback speed controls

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

### Frontend Enhancements
-   **[ ] User Authentication UI:**
    -   Login/signup forms
    -   Profile management
    -   History of processed videos
-   **[ ] Advanced Visualization Features:**
    -   Detailed data flow visualization
    -   Agent logs viewer
    -   Process analytics
-   **[ ] Advanced Audio Player Controls:**
    -   Playback speed, skip forward/backward.
    -   Transcript synchronization
    -   Highlight current section being played
-   **[ ] Display Transcript Snippets:**
    -   Show parts of the transcript alongside the summary.
    -   Searchable transcript
-   **[ ] Shareable Links to Summaries:**
    -   Generate unique links for users to share their audio summaries.
-   **[ ] Offline Support:**
    -   PWA capabilities
    -   Local storage for history
    -   Service workers for caching

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
