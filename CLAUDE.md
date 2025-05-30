# CLAUDE.md

This file provides essential context and guidance to Claude Code (claude.ai/code) when working with the Podcast Digest Agent project. It contains frequently needed commands, architecture details, and project-specific conventions that should be referenced in every coding session.

## Common Development Commands

### Backend Development (Python/FastAPI)
```bash
# Setup
cd server
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
cd client
npm install
npm run dev                        # Development with Turbopack
npm run build                      # Production build
npm run lint                       # ESLint
```

### Full System Development
```bash
# Start both services (2 terminals):
# Terminal 1: cd server && python src/main.py
# Terminal 2: cd client && npm run dev
```

## Architecture Overview

### ADK-Based Processing Pipeline
The core system uses Google's Agent Development Kit (ADK) for podcast processing:

**PodcastDigestAgent** → **TranscriptAgent** → **DialogueAgent** → **AudioAgent**

- Uses Google ADK v1.0.0 for agent orchestration
- Gemini 2.0 Flash for fast LLM inference
- Processing is asynchronous with real-time status updates via WebSocket
- Each agent reports progress through the ADK event system

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

## Current Project Status

**Production-Ready System**: The podcast digest pipeline is fully functional with end-to-end processing of YouTube videos into audio digests.

**Tech Stack**:
- **Backend**: FastAPI with Python 3.11+, Google Generative AI (Gemini), Google Cloud TTS
- **Frontend**: Next.js 15 with TypeScript, shadcn/ui, TanStack Query, Motion.dev
- **Real-time**: WebSocket for live processing updates
- **Testing**: Pytest with 85%+ coverage requirement

**Key Features**:
- ADK-based pipeline processing using Google's official agent framework
- Real-time visualization of processing status
- RESTful API with comprehensive endpoints
- WebSocket integration for live updates
- Conversational audio output with dual voices using Chirp HD

**Important Files**:
- ADK Agents: `server/src/adk_agents/`
- ADK Pipeline: `server/src/adk_runners/pipeline_runner.py`
- API endpoints: `server/src/api/v1/`
- Frontend app: `client/src/`
- Configuration: `.env` file required with Google Cloud credentials

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

**ADK Agent Communication**: Agents communicate through the ADK event system and session state.

**WebSocket Integration**: `AdkWebSocketBridge` connects ADK events to WebSocket connections, broadcasting real-time updates.

**Frontend State Management**: `WorkflowContext` manages processing state, with `ProcessingVisualizer` component handling real-time visualization updates.

**Audio Processing**: Uses Google Cloud TTS with Chirp HD voices for high-quality conversational output.

**Error Handling**: ADK provides robust error handling with automatic retries and graceful degradation.

## Common Troubleshooting

**Environment Setup**:
```bash
# Required environment variables in .env:
GOOGLE_API_KEY=your-google-api-key
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

**Common Issues**:
- **Import errors**: Ensure virtual environment is activated
- **Google API errors**: Check API key and quotas
- **WebSocket connection issues**: Verify CORS settings
- **Audio generation fails**: Check Google Cloud TTS credentials

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

## Quick Reference

**File Structure**:
```
server/
├── src/
│   ├── adk_agents/      # ADK agent implementations
│   ├── adk_runners/     # ADK pipeline orchestration
│   ├── adk_tools/       # ADK-compatible tools
│   ├── api/v1/          # FastAPI endpoints
│   ├── config/          # Configuration and settings
│   ├── core/            # Core services (WebSocket, task management)
│   └── models/          # Pydantic models

client/
├── src/
│   ├── app/             # Next.js app router pages
│   ├── components/      # React components
│   ├── contexts/        # State management (WorkflowContext)
│   └── lib/             # Utilities and API client
```

## New Project Structure (Client/Server)

The project has been reorganized into a clear client/server architecture:

- **client/**: All frontend code (formerly podcast-digest-ui/)
- **server/**: All backend code (formerly src/)
- **tests/**: Test files (kept in root)
- **specs/**: Project specifications and PRDs
- **docs/**: Architecture and API documentation

### Updated Commands

Backend development:
```bash
cd server
python src/main.py
```

Frontend development:
```bash
cd client
npm run dev
```
