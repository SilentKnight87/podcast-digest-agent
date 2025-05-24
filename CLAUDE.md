# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Backend Development (Python/FastAPI)
```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r dev-requirements.txt

# Start backend server
python src/main.py  # API at http://localhost:8000, docs at /docs

# Testing
pytest                              # All tests
pytest --cov=src                   # With coverage
pytest tests/agents/               # Specific directory
pytest -k "test_summarizer"        # Pattern matching

# Code Quality
black src/                         # Format code
ruff check src/                    # Lint
ruff check --fix src/             # Auto-fix
mypy src/                         # Type checking

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### Frontend Development (Next.js)
```bash
# Setup and run
cd podcast-digest-ui
npm install
npm run dev                        # Development with Turbopack
npm run build                      # Production build
npm run lint                       # ESLint
```

### Full System Development
```bash
# Start both services (2 terminals):
# Terminal 1: python src/main.py
# Terminal 2: cd podcast-digest-ui && npm run dev

# CLI processing (alternative to web interface)
echo "https://youtube.com/watch?v=example" > input/youtube_links.txt
python src/runners/simple_pipeline.py
```

## Architecture Overview

### Agent-Based Processing Pipeline
The core system uses a sequential agent pipeline for podcast processing:

**TranscriptFetcher** → **SummarizerAgent** → **SynthesizerAgent** → **AudioGenerator**

- All agents inherit from `BaseAgent` and use Google Generative AI (Gemini models)
- Processing is asynchronous with real-time status updates via WebSocket
- Each agent tracks progress, logs, and status independently

### API Architecture
- **FastAPI backend** with `/api/v1/` REST endpoints
- **WebSocket** real-time updates at `/api/v1/ws/status/{task_id}`
- **Background task processing** using FastAPI's BackgroundTasks
- **Task management** via `TaskManager` for status tracking across agents

### Frontend-Backend Communication
- **Next.js 15** with App Router and TypeScript
- **Axios** for HTTP requests to FastAPI
- **WebSocket** for live processing updates
- **@tanstack/react-query** for data fetching and caching
- **TypeScript interfaces** mirror Pydantic models for type safety

### Real-time Processing Visualization
- Interactive node-based workflow visualization
- Particle animations between processing nodes using Motion.dev
- Live agent status updates (pending → running → completed/error)
- WebSocket-driven state management via React Context

## Project Overview

Podcast Digest Agent is a system for processing YouTube podcast links, fetching transcripts, generating summaries, synthesizing conversational scripts, and creating audio digests. The project uses a pipeline of specialized agents to transform podcast content into an easily consumable audio format.

## Development Memories

- Always use context7 mcp to get the latest library documentation, and to get the latest patterns and standards, best practices etc.
- Make small incremental changes and test thoroughly after each step when implementing a feature
- **README.md Maintenance**: When implementing new features, updating architecture, or changing core functionality, automatically update the README.md file to reflect these changes. Follow industry standards for README documentation including badges, clear installation instructions, usage examples, and comprehensive project structure documentation.

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

**Current Implementation Status**:
- ✅ **Frontend-Backend Integration**: Complete with WebSocket real-time updates
- ✅ **Agent Pipeline**: Functional end-to-end processing (TranscriptFetcher, SummarizerAgent, SynthesizerAgent, AudioGenerator)
- ✅ **Web Interface**: Next.js frontend with processing visualization and audio playback
- ✅ **API Layer**: FastAPI with comprehensive endpoints for processing, status, history, and configuration
- ✅ **Real-time Updates**: WebSocket implementation for live progress tracking
- ✅ **Testing Suite**: Comprehensive test coverage for agents, API endpoints, and core functionality

**Pending Cleanup**: Two PRDs created for systematic cleanup:
- `GOOGLE_ADK_MIGRATION_PRD.md`: Future migration to Google ADK for learning

**Latest Updates**:
- Updated README.md with comprehensive documentation following industry standards
- Added proper badges, installation instructions, API documentation, and troubleshooting guide
- Documented complete project structure and configuration options
- Included development guidelines and contribution instructions

## Code Quality Standards

**Testing Requirements**:
- Follow Test-Driven Development (TDD) approach for new features
- Maintain high test coverage (>85% for core modules)
- Write tests before implementation code
- Use pytest for backend testing, ensure all tests pass before commits

**Code Style Requirements**:
- Use Black for code formatting (line length: 100)
- Use Ruff for linting with configured rules
- Use MyPy for type checking with strict settings
- Add type hints for all function signatures
- Write comprehensive docstrings for public APIs

**Development Workflow**:
```bash
# Before implementing new features
pytest                    # Ensure all tests pass
ruff check src/          # Check linting
black src/               # Format code
mypy src/                # Type checking

# During development
pytest tests/specific_test.py  # Run relevant tests

# Before committing
pytest --cov=src         # Verify coverage
ruff check --fix src/    # Auto-fix linting issues
```

### Key Configuration Details

**Pre-commit hooks** are configured for automatic code quality:
- Trailing whitespace and end-of-file fixes
- Ruff linting with auto-fix
- Black formatting
- MyPy type checking (src/ only, excludes tests/)

**Test isolation**: Tests use temporary directories and mock Google Cloud services. Set `PODCAST_AGENT_TEST_MODE=true` to enable test mode.

**Google Cloud Authentication**: Use service account JSON or `gcloud auth application-default login`.

**API Development Standards**:
- Use Pydantic models for all request/response schemas
- Implement comprehensive error handling with meaningful messages
- Add OpenAPI documentation for all endpoints
- Use FastAPI dependency injection for shared services
- Implement WebSocket for real-time features where appropriate

**Frontend Development Standards**:
- Use TypeScript for all components and utilities
- Follow React best practices with proper state management
- Use shadcn/ui components for consistent design
- Implement responsive design with Tailwind CSS
- Add proper error boundaries and loading states

## Key Implementation Details

**Agent Communication**: Agents don't communicate directly - the pipeline runner (`simple_pipeline.py`) orchestrates data flow between agents sequentially.

**WebSocket Integration**: `ConnectionManager` tracks active WebSocket connections per task_id and broadcasts status updates to connected clients.

**Frontend State Management**: `WorkflowContext` manages processing state, with `ProcessingVisualizer` component handling real-time visualization updates.

**Audio Processing**: Uses Google Cloud TTS with two distinct voices (male/female) for conversational output, with `pydub` for audio concatenation.

**Error Handling**: Each agent has independent error handling - failures in one agent don't crash the entire pipeline, but mark the task as failed.

## Deployment and Maintenance

**Environment Management**:
- Use `.env` files for configuration
- Document all environment variables in README.md
- Provide example configurations for different deployment scenarios

**Documentation Maintenance**:
- Keep README.md updated with latest features and changes
- Update API documentation when endpoints change
- Maintain project specifications in `/specs` directory
- Document breaking changes and migration guides
