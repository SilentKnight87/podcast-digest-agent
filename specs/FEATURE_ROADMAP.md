# Podcast Digest Agent - Feature Roadmap

This document outlines the planned features and development phases for the Podcast Digest Agent project.

## Overall Project Goal

To create a web application that allows users to input YouTube video URLs, process them to generate a summarized audio digest, and play the audio back to the user.

## Phase 1: Core Backend API & Basic API Functionality

### Backend (Python/FastAPI)
-   **[ ] API Endpoint for URL Submission:**
    -   `POST /api/v1/process_youtube_url`
    -   Accepts: YouTube URL.
    -   Action: Triggers the backend processing pipeline (transcription, summarization, TTS).
    -   Returns: A task ID for status polling.
-   **[ ] API Endpoint for Status Polling:**
    -   `GET /api/v1/status/{task_id}`
    -   Accepts: Task ID.
    -   Returns: Current status (e.g., "processing", "completed", "failed") and, if completed, the URL to the audio file.
-   **[ ] API Endpoint for Serving Audio:**
    -   `GET /audio/{filename.mp3}`
    -   Serves generated audio files from the `output_audio/` directory.
-   **[ ] Core Processing Logic Integration:**
    -   Integrate existing YouTube transcription.
    -   Integrate summarization agent.
    -   Integrate `audio_tools.py` for Text-to-Speech (TTS) using Google Cloud.
-   **[ ] Asynchronous Task Handling:**
    -   Implement a robust way to handle long-running processing tasks in the background (e.g., using FastAPI's background tasks or a dedicated task queue like Celery).
-   **[ ] Configuration Management:**
    -   Securely manage API keys and configurations (e.g., using `.env` files and Pydantic settings).
-   **[ ] Basic Error Handling:**
    -   Implement error handling for common issues (invalid URLs, API failures, processing errors).

## Phase 2: Enhanced Frontend Development (Next.js + shadcn/ui)

### Frontend Setup & Base Components
-   **[ ] Next.js Project Setup:**
    -   Initialize Next.js 14+ app with App Router
    -   Configure TypeScript
    -   Set up Tailwind CSS
    -   Install shadcn/ui component system
    -   Configure Lucide icons
-   **[ ] Design System Implementation:**
    -   Implement color palette, typography, and spacing system
    -   Create theme provider for dark/light mode
    -   Create base layout components
    -   Set up responsive breakpoints

### Core UI Development
-   **[ ] Homepage & Layout Components:**
    -   Navbar with theme switcher
    -   Hero section with URL input
    -   Section layout components
    -   Footer
-   **[ ] URL Input & Validation:**
    -   Form components with validation
    -   Error handling and feedback
    -   Submit functionality
-   **[ ] Basic Process Visualization:**
    -   Static process timeline for non-processing state
    -   Basic processing status indicators
-   **[ ] Audio Player Implementation:**
    -   Enhanced audio player component
    -   Play/pause/seek controls
    -   Audio visualization

### Agent Workflow Visualization
-   **[ ] Agent Workflow Data Models:**
    -   Define TypeScript interfaces for agent states and data flow
    -   Create context provider for workflow state
-   **[ ] Agent Visualization Components:**
    -   ProcessTimeline component for static view
    -   ProcessingVisualizer for active processing
    -   Progress indicators for overall and per-agent progress
-   **[ ] Flow Animation & Visual Effects:**
    -   Framer Motion animations for data flow visualization
    -   Status-based styling and transitions
    -   Interactive elements (hover states, click actions)
-   **[ ] Responsive Adaptations:**
    -   Mobile-friendly linear visualization
    -   Tablet and desktop optimized layouts
    -   Accessibility considerations

### WebSocket Integration
-   **[ ] WebSocket Client Setup:**
    -   Implement WebSocket connection management
    -   Connection status indicators
    -   Reconnection logic
-   **[ ] Real-time Update Handling:**
    -   Process WebSocket messages
    -   Update UI state based on backend events
    -   Handle connection errors

### Results Display
-   **[ ] Summary Display Components:**
    -   SummaryCard layout
    -   Key points visualization
    -   Quote formatting
-   **[ ] Enhanced Audio Integration:**
    -   Audio player with transcript integration
    -   Progress tracking
    -   Playback speed controls

## Phase 3: Advanced Features & Scalability

### Backend Enhancements
-   **[ ] WebSocket Server Implementation:**
    -   Set up WebSocket endpoint for real-time updates
    -   Implement event emission for agent status changes
    -   Include detailed progress information
-   **[ ] Detailed Agent Status Tracking:**
    -   Enhanced data model for agent statuses
    -   Per-agent progress tracking
    -   Timing measurements
-   **[ ] User Accounts & Authentication (Optional):**
    -   Allow users to create accounts to save their history.
-   **[ ] Database Integration:**
    -   Store task information, user data, and metadata about processed videos in a database.
-   **[ ] Customizable Summarization Options:**
    -   Allow users to specify summarization length or style (if feasible).
-   **[ ] Choice of Voices for TTS:**
    -   Allow users to select different voices for the audio output.
-   **[ ] Scalability Improvements:**
    -   Optimize backend for handling more concurrent requests (e.g., worker scaling, database optimizations).
    -   Consider serverless functions for parts of the pipeline.
-   **[ ] Logging & Monitoring:**
    -   Implement comprehensive logging and monitoring for the backend services.

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


## Future Ideas & Considerations


-   **[ ] Batch Processing of Multiple URLs.**
