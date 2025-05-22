# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Podcast Digest Agent is a system for processing YouTube podcast links, fetching transcripts, generating summaries, synthesizing conversational scripts, and creating audio digests. The project uses a pipeline of specialized agents to transform podcast content into an easily consumable audio format.

The architecture consists of:
1. A Python backend (FastAPI) with specialized agents
2. A Next.js frontend for user interaction
3. A WebSocket-based real-time update system

## Development Memories

- Always use context7 mcp to get the latest library documentation, and to get the latest patterns and standards, best practices etc.

## Current Project Status (Updated)

**Working System**: The podcast processing pipeline is currently functional and processes real YouTube videos end-to-end.

**Critical Issues Resolved**:
1. **Pipeline Implementation Bug**: The API was incorrectly using simulation code (`src.processing.pipeline`) instead of the real implementation (`src.runners.pipeline_runner`). Fixed by updating `src/api/v1/endpoints/tasks.py`.
2. **Google AI Content Object Bug**: Agents had incorrect Content object creation causing API failures. Fixed by using simple string prompts instead of Content/Part objects.
3. **URL Construction Bug**: Frontend 404 errors fixed by proper API endpoint URL handling.

**Architecture Complexity Issues Identified**:
- 601+ lines of unnecessary simulation code in `/src/processing/` 
- Overly complex 467-line `pipeline_runner.py` that needs simplification
- Multiple redundant pipeline implementations causing confusion

**Pending Cleanup**: Two PRDs created for systematic cleanup:
- `BACKEND_CLEANUP_PRD.md`: Immediate cleanup of simulation files and pipeline simplification
- `GOOGLE_ADK_MIGRATION_PRD.md`: Future migration to Google ADK for learning

## Development Commands

### Backend (Python)

#### Environment Setup
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

#### Running the API Server
```bash
# Start the FastAPI server with hot reload
uvicorn src.main:app --reload
```

#### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run a specific test file
pytest tests/agents/test_audio_generator.py

# Run a specific test function
pytest tests/agents/test_audio_generator.py::test_agent_initialization
```

### Frontend (Next.js)

#### Environment Setup
```bash
# Navigate to the frontend directory
cd podcast-digest-ui

# Install dependencies
npm install
```

#### Running the UI Server
```bash
# Start the development server
npm run dev

# Start with Turbopack for faster builds
npm run dev -- --turbopack
```

#### Build for Production
```bash
# Build the frontend
npm run build

# Start the production server
npm start
```

## Architecture Overview

### Backend Components

1. **Agents**: Specialized processing components
   - `TranscriptFetcher`: Extracts text from YouTube videos
   - `SummarizerAgent`: Generates concise summaries
   - `SynthesizerAgent`: Creates conversational dialogue
   - `AudioGenerator`: Converts text to speech using Google Cloud TTS

2. **Pipeline**: Orchestrates the processing flow
   - `PipelineRunner`: Located in `src/runners/pipeline_runner.py` - the REAL implementation (467 lines, needs simplification)
   - **AVOID**: `src/processing/pipeline.py` - simulation code that should be removed

3. **API Layer**: Handles client interactions
   - RESTful endpoints for task submission and status retrieval
   - WebSocket connection for real-time updates

4. **Core Services**:
   - `task_manager`: Tracks task progress and status
   - `connection_manager`: Manages WebSocket connections

### Frontend Components

1. **Layout**: Basic page structure
   - `HeroSection`: Main interaction area for URL input
   - `Navbar` and `Footer`: Navigation and branding

2. **Process**: Visualization of processing pipeline
   - `ProcessingVisualizer`: Node-based visualization of the agent workflow
   - `ProcessTimeline`: Timeline representation of processing stages

3. **Results**: Output display
   - `PlayDigestButton`: Audio playback interface

4. **State Management**:
   - `WorkflowContext`: Manages the state of the processing workflow

## Key Files and Folders

- `/src/`: Backend Python code
  - `/src/agents/`: Specialized agent implementations
  - `/src/api/`: API endpoints and routers
  - `/src/config/`: Configuration and settings
  - `/src/core/`: Core services and managers
  - `/src/models/`: Pydantic data models
  - `/src/tools/`: Utility functions and tools
  - `/src/runners/`: **REAL** pipeline implementation (use this)
  - `/src/processing/`: **SIMULATION** code (scheduled for removal)

- `/podcast-digest-ui/`: Frontend Next.js application
  - `/podcast-digest-ui/src/components/`: UI components
  - `/podcast-digest-ui/src/contexts/`: React context providers
  - `/podcast-digest-ui/src/app/`: Next.js pages and layouts

- `/tests/`: Backend test suite
  - Test files mirror the structure of the `/src/` directory

## Environment Variables

The project uses environment variables for configuration:

### Backend
- `DEBUG`: Enable debug mode (default: False)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Google Cloud credentials JSON file
- `OUTPUT_AUDIO_DIR`: Directory for audio output (default: "output_audio")
- `INPUT_DIR`: Directory for input files (default: "input")
- `PODCAST_AGENT_TEST_MODE`: Set to "True" for running tests

### Frontend
- `NEXT_PUBLIC_API_URL`: Base URL for the backend API

## Testing Guidelines

- Always write tests for new features and bug fixes
- Use pytest fixtures and mocks for external dependencies
- Tests should be isolated and not depend on external services
- Test both success and failure paths
- In test mode, temporary directories are used for input and output

### Known Test Issues

- **WebSocket Test Issue**: In WebSocket tests, the `WebSocketTestSession` object from `starlette.testclient` doesn't match the `WebSocket` object from FastAPI stored in the connection manager. This causes equality comparison to fail in tests like `test_websocket_connect_disconnect`.

### Critical Fixes Applied

- **Google AI Content Object Bug**: Agents were incorrectly creating `Content(parts=[Part(text=prompt_text)])` objects, causing Google AI API failures. **FIXED**: Use simple string prompts directly instead of Content objects.
- **Pipeline Selection Bug**: API was using simulation pipeline instead of real implementation. **FIXED**: Import from `src.runners.pipeline_runner` not `src.processing.pipeline`.

## Common Development Workflows

1. **Adding a New Agent**:
   - Create a new agent class in `/src/agents/`
   - Implement the agent's processing logic
   - Register the agent in the pipeline
   - Write tests in `/tests/agents/`

2. **Extending the API**:
   - Add new endpoint to appropriate router
   - Create Pydantic model for request/response
   - Implement validation and error handling
   - Update task manager if needed
   - Add tests for the new endpoint

3. **Adding UI Components**:
   - Create new component in `/podcast-digest-ui/src/components/`
   - Use Tailwind CSS for styling
   - Update WorkflowContext if needed
   - Connect to API via React Query hooks

## Important Development Notes

**DO NOT USE THESE FILES** (simulation code scheduled for removal):
- `src/processing/pipeline.py`
- `src/processing/pipeline_simulation_backup.py`
- Any other files in `src/processing/`

**ALWAYS USE**:
- `src/runners/pipeline_runner.py` for pipeline implementation
- Simple string prompts for Google AI agents (not Content objects)
- Real YouTube processing, not simulation/placeholder content

**Before Making Changes**:
- Check if you're working with simulation vs real implementation
- Verify Google AI agents use simple string prompts
- Ensure API endpoints import from `src.runners` not `src.processing`