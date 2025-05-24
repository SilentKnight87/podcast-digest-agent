# Code Cleanup & Backend Cleanup PRD

## Overview

This specification outlines a comprehensive cleanup plan for the Podcast Digest Agent codebase to prepare it for deployment. The cleanup includes removing simulation files, simplifying the pipeline runner, eliminating redundant code, addressing technical debt, improving code quality, and standardizing patterns.

## Goals

1. **Backend Cleanup**: Remove simulation files and redundant code (601+ lines)
2. **Pipeline Simplification**: Reduce pipeline runner from 467 to ~100 lines
3. **Code Quality**: Standardize formatting, resolve deprecation warnings
4. **Type Safety**: Improve type annotations and error handling
5. **Performance**: Optimize resource usage and maintain functionality
6. **Code Organization**: Remove unused code and dependencies
7. **Testing**: Implement small changes with testing after each step
8. **Quality Gates**: Set up linting/formatting tools and pre-commit hooks

## Implementation Strategy

**Testing Approach**: Make small incremental changes and test thoroughly after each step. Run the entire workflow after completing each phase to ensure no regression.

**Safety First**: Only delete unused code, components, directories, and files with high certainty they won't break the system. When uncertain, ask for user confirmation before deletion.

## Implementation Details

### Phase 1: Backend Cleanup & Simulation Removal (30 minutes)

#### Remove Simulation Files and Redundant Code

The current backend has accumulated unnecessary simulation files that need to be removed.

##### Files to Delete Completely

1. **`/src/processing/pipeline_simulation_backup.py`** - 601 lines of pure simulation code
2. **`/src/tools/summarization_tools.py`** - Redundant with SummarizerAgent
3. **`/src/tools/synthesis_tools.py`** - Redundant with SynthesizerAgent
4. **`/src/utils/audio_placeholder.py`** - Placeholder logic no longer needed

##### Safety Check Commands

```bash
# Check if these files are imported/used anywhere
grep -r "pipeline_simulation_backup" src/ --exclude-dir=__pycache__
grep -r "summarization_tools" src/ --exclude-dir=__pycache__
grep -r "synthesis_tools" src/ --exclude-dir=__pycache__
grep -r "audio_placeholder" src/ --exclude-dir=__pycache__
```

##### Deletion Commands (Only if safe)

```bash
# Navigate to project root
cd /Users/peterbrown/Documents/Code/podcast-digest-agent

# Remove simulation files (only if grep shows no usage)
rm src/processing/pipeline_simulation_backup.py
rm src/tools/summarization_tools.py
rm src/tools/synthesis_tools.py
rm src/utils/audio_placeholder.py

# Verify files are removed
ls -la src/processing/
ls -la src/tools/
ls -la src/utils/
```

##### Test After Deletion

```bash
# Test that the system still works
uvicorn src.main:app --reload &
# Test API endpoints to ensure no import errors
curl -X GET "http://localhost:8000/api/v1/status"
```

#### Simplify Pipeline Runner (2-3 hours)

The current pipeline runner (`/src/runners/pipeline_runner.py`) is overly complex with 467 lines. We'll create a simplified version and gradually migrate.

##### Current Issues
- **467 lines** of overly complex orchestration
- Unnecessary helper methods and complex error handling
- Over-engineered result processing
- Complex temporary directory management

##### Create Simplified Pipeline

**New file**: `/src/runners/simple_pipeline.py` (~100 lines)

```python
"""
Simplified Pipeline Runner for podcast digest generation.
"""
import logging
import asyncio
import tempfile
import shutil
import json
from typing import List, Dict, Any
from pathlib import Path

from src.agents.transcript_fetcher import TranscriptFetcher
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.audio_generator import AudioGenerator
from src.tools.transcript_tools import fetch_transcripts
from src.tools.audio_tools import generate_audio_segment_tool, combine_audio_segments_tool
from google.cloud import texttospeech_v1

logger = logging.getLogger(__name__)

class SimplePipeline:
    """Simplified pipeline orchestrator for podcast digest generation."""

    def __init__(self):
        """Initialize with agents."""
        self.transcript_fetcher = TranscriptFetcher()
        self.summarizer = SummarizerAgent()
        self.synthesizer = SynthesizerAgent()
        self.audio_generator = AudioGenerator()
        self.temp_dirs: List[str] = []
        logger.info("SimplePipeline initialized")

    async def run_async(self, video_ids: List[str], output_dir: str) -> Dict[str, Any]:
        """Run the complete pipeline asynchronously."""
        logger.info(f"Starting pipeline for {len(video_ids)} videos")

        try:
            async with texttospeech_v1.TextToSpeechAsyncClient() as tts_client:
                # Step 1: Fetch transcripts
                transcript_results = fetch_transcripts.run(video_ids=video_ids)
                transcripts = self._extract_successful_transcripts(transcript_results)

                if not transcripts:
                    return self._error_result("No transcripts fetched", video_ids)

                # Step 2: Summarize transcripts
                summaries = await self._summarize_transcripts(list(transcripts.values()))

                if not summaries:
                    return self._error_result("No summaries generated", video_ids)

                # Step 3: Synthesize dialogue
                dialogue = await self._synthesize_dialogue(summaries)

                if not dialogue:
                    return self._error_result("No dialogue generated", video_ids)

                # Step 4: Generate audio
                audio_path = await self._generate_audio(dialogue, output_dir, tts_client)

                if not audio_path:
                    return self._error_result("Audio generation failed", video_ids)

                return {
                    "status": "success",
                    "success": True,
                    "dialogue_script": dialogue,
                    "final_audio_path": audio_path,
                    "summary_count": len(summaries),
                    "failed_transcripts": [],
                    "error": None
                }

        except Exception as e:
            logger.exception(f"Pipeline error: {e}")
            return self._error_result(f"Pipeline error: {e}", video_ids)
        finally:
            self._cleanup()

    def _extract_successful_transcripts(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Extract successful transcripts from results."""
        transcripts = {}
        for video_id, result in results.items():
            if isinstance(result, dict) and result.get("success"):
                transcript = result.get("transcript", "")
                if transcript:
                    transcripts[video_id] = transcript
        return transcripts

    async def _summarize_transcripts(self, transcripts: List[str]) -> List[str]:
        """Summarize all transcripts."""
        summaries = []
        for transcript in transcripts:
            try:
                async for event in self.summarizer.run_async(transcript):
                    if event.type.name == "RESULT" and "summary" in event.payload:
                        summaries.append(event.payload["summary"])
                        break
            except Exception as e:
                logger.error(f"Summarization failed: {e}")
        return summaries

    async def _synthesize_dialogue(self, summaries: List[str]) -> List[Dict[str, Any]]:
        """Synthesize dialogue from summaries."""
        try:
            summaries_json = json.dumps(summaries)
            async for event in self.synthesizer.run_async(summaries_json):
                if event.type.name == "RESULT" and "dialogue" in event.payload:
                    return event.payload["dialogue"]
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
        return []

    async def _generate_audio(self, dialogue: List[Dict[str, Any]], output_dir: str, tts_client) -> str:
        """Generate final audio from dialogue."""
        try:
            # Create temp directory for segments
            temp_dir = tempfile.mkdtemp(prefix="podcast_segments_")
            self.temp_dirs.append(temp_dir)

            # Generate individual segments
            tasks = []
            for i, segment in enumerate(dialogue):
                speaker = segment.get("speaker", "A")
                line = segment.get("line", "")
                if line:
                    output_path = Path(temp_dir) / f"segment_{i:03d}_{speaker}.mp3"
                    task = generate_audio_segment_tool.run(
                        text=line,
                        speaker=speaker,
                        output_filepath=str(output_path),
                        tts_client=tts_client
                    )
                    tasks.append(task)

            # Wait for all segments
            segment_files = await asyncio.gather(*tasks, return_exceptions=True)
            valid_segments = [f for f in segment_files if isinstance(f, str)]

            if not valid_segments:
                return None

            # Combine segments
            final_path = await combine_audio_segments_tool.run(
                segment_filepaths=valid_segments,
                output_dir=output_dir
            )

            return final_path

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None

    def _error_result(self, error_msg: str, video_ids: List[str]) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "status": "error",
            "success": False,
            "dialogue_script": [],
            "final_audio_path": None,
            "summary_count": 0,
            "failed_transcripts": video_ids,
            "error": error_msg
        }

    def _cleanup(self) -> None:
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Cleanup failed for {temp_dir}: {e}")
        self.temp_dirs.clear()

    def run_pipeline(self, video_ids: List[str], output_dir: str = "./output_audio") -> Dict[str, Any]:
        """Synchronous wrapper for async pipeline."""
        return asyncio.run(self.run_async(video_ids, output_dir))
```

##### Test New Pipeline

```bash
# Test the new pipeline in isolation
python -c "
from src.runners.simple_pipeline import SimplePipeline
pipeline = SimplePipeline()
result = pipeline.run_pipeline(['test_video_id'])
print('Pipeline test completed:', result.get('status'))
"
```

### Phase 2: Backend (Python) Code Cleanup

#### 2.1 Setup Linting/Formatting Tools

**Install and configure linting tools:**

```bash
# Install Python linting tools
pip install black ruff mypy

# Install pre-commit for automated checks
pip install pre-commit
```

**Configure tools:**

```toml
# pyproject.toml additions
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "B", "I", "N", "PYI", "UP", "TID"]
ignore = []

[tool.ruff.isort]
known-first-party = ["src"]

[tool.black]
line-length = 100
target-version = ["py311"]
include = '\.pyi?$'

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Test linting setup:**

```bash
# Run linting on the codebase
ruff check src/
black --check src/
mypy src/
```

#### 2.2 Fix Pydantic V2 Compatibility Issues

Current issues include using deprecated methods like `.dict()` instead of `.model_dump()`:

```python
# Before:
response_data = model_instance.dict()

# After:
response_data = model_instance.model_dump()
```

Update all instances across the codebase:

1. `src/core/task_manager.py`
2. `src/api/v1/endpoints/tasks.py`
3. Any other files using `.dict()`

#### 2.3 Type Annotations and Validation

Improve type annotations throughout the codebase:

```python
# Before:
def process_data(data):
    # Processing logic

# After:
def process_data(data: dict[str, Any]) -> ProcessedResult:
    # Processing logic with validation
    if "required_key" not in data:
        raise ValueError("Missing required_key in data")
    # Processing logic
```

Focus areas:
- Agent class methods
- API endpoints
- Utility functions

#### 2.4 Error Handling Improvements

Implement consistent error handling patterns:

```python
# Before:
try:
    result = process_data(data)
except Exception as e:
    logger.error(f"Error: {e}")
    raise

# After:
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data format: {e}")
    raise InvalidDataError(f"Data validation failed: {e}") from e
except IOError as e:
    logger.error(f"I/O error during processing: {e}")
    raise ServiceUnavailableError("Service temporarily unavailable") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise InternalServerError("An unexpected error occurred") from e
```

Create a custom exception hierarchy:

```python
# src/exceptions.py
class PodcastDigestError(Exception):
    """Base exception for all application errors."""

class InvalidDataError(PodcastDigestError):
    """Raised when input data is invalid."""

class ServiceUnavailableError(PodcastDigestError):
    """Raised when a service dependency is unavailable."""

class InternalServerError(PodcastDigestError):
    """Raised when an unexpected error occurs."""
```

#### 2.5 Code Organization and Structure

Implement consistent module structure:

```
src/
  __init__.py   # Package exports
  exceptions.py # Custom exceptions
  models/       # Data models
  core/         # Core business logic
  api/          # API endpoints
  agents/       # Agent implementations
  tools/        # Tool implementations
  config/       # Configuration
  utils/        # Utility functions
```

Create clear import hierarchy to avoid circular dependencies.

#### 2.6 Configuration Management

Refactor configuration management:

```python
# src/config/settings.py
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    # Use ConfigDict instead of class Config
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    APP_NAME: str = "Podcast Digest Agent"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    # Other settings...
```

### Phase 3: API Integration Update (30 minutes)

Update the API endpoint to use the new simplified pipeline.

#### Update `/src/api/v1/endpoints/tasks.py`

Replace the import and function usage:

```python
# Replace this import:
# from src.runners.pipeline_runner import PipelineRunner

# With this import:
from src.runners.simple_pipeline import SimplePipeline

# In the run_real_processing_pipeline function, replace:
# pipeline_runner = PipelineRunner(
#     transcript_fetcher=transcript_fetcher,
#     summarizer=summarizer,
#     synthesizer=synthesizer,
#     audio_generator=audio_generator
# )

# With:
pipeline = SimplePipeline()

# Replace:
# result = await pipeline_runner.run_pipeline_async(
#     video_ids=[video_id],
#     output_dir=settings.OUTPUT_AUDIO_DIR
# )

# With:
result = await pipeline.run_async(
    video_ids=[video_id],
    output_dir=settings.OUTPUT_AUDIO_DIR
)

# Replace cleanup call:
# if 'pipeline_runner' in locals():
#     pipeline_runner.cleanup()

# With:
# Cleanup is handled automatically in the SimplePipeline
```

#### Test API Integration

```bash
# Start the backend server
uvicorn src.main:app --reload &

# Test the API endpoint
curl -X POST "http://localhost:8000/api/v1/tasks/process_youtube_url" \
-H "Content-Type: application/json" \
-d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Phase 4: Frontend (Next.js) Code Cleanup

#### 4.1 Setup Frontend Linting/Formatting

**Install frontend linting tools:**

```bash
cd podcast-digest-ui
npm install --save-dev eslint prettier @typescript-eslint/parser @typescript-eslint/eslint-plugin eslint-plugin-react eslint-plugin-react-hooks
```

**Configure ESLint and Prettier:**

```javascript
// eslint.config.mjs
export default [
  {
    extends: [
      'eslint:recommended',
      'plugin:@typescript-eslint/recommended',
      'plugin:react/recommended',
      'plugin:react-hooks/recommended',
      'next/core-web-vitals',
    ],
    plugins: ['@typescript-eslint', 'react', 'react-hooks'],
    rules: {
      // Custom rules
    },
  },
];
```

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "printWidth": 100,
  "trailingComma": "es5"
}
```

**Test frontend linting:**

```bash
npm run lint
npx prettier --check src/
```

#### 4.2 Component Organization

Implement consistent component structure:

```
src/
  components/
    common/       # Reusable UI components
    layout/       # Layout components
    features/     # Feature-specific components
      podcast/    # Podcast-related components
      audio/      # Audio-related components
  hooks/          # Custom React hooks
  contexts/       # React context providers
  lib/            # Utility libraries
  types/          # TypeScript type definitions
  styles/         # Global styles
```

#### 4.3 TypeScript Improvements

Improve type definitions:

```typescript
// Before:
interface WorkflowState {
  agents: any[];
  dataFlows: any[];
  timeline: any[];
  // Other properties...
}

// After:
interface Agent {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  startTime?: string;
  endTime?: string;
  logs: AgentLog[];
}

interface DataFlow {
  id: string;
  fromAgentId: string;
  toAgentId: string;
  status: 'pending' | 'transferring' | 'completed' | 'error';
  metadata?: Record<string, unknown>;
}

interface TimelineEvent {
  timestamp: string;
  event: 'agent_started' | 'agent_completed' | 'progress_update' | 'process_started' | 'process_completed' | 'process_failed';
  agentId?: string;
  message: string;
}

interface WorkflowState {
  agents: Agent[];
  dataFlows: DataFlow[];
  timeline: TimelineEvent[];
  // Other properties...
}
```

#### 4.4 State Management Refactoring

Replace direct state mutations with immutable patterns:

```typescript
// Before:
function updateAgent(agentId, update) {
  setWorkflowState(prevState => {
    const updatedState = JSON.parse(JSON.stringify(prevState));
    const agentIndex = updatedState.agents.findIndex(a => a.id === agentId);
    if (agentIndex !== -1) {
      updatedState.agents[agentIndex] = {
        ...updatedState.agents[agentIndex],
        ...update
      };
    }
    return updatedState;
  });
}

// After:
function updateAgent(agentId: string, update: Partial<Agent>) {
  setWorkflowState(prevState => {
    if (!prevState) return prevState;

    return {
      ...prevState,
      agents: prevState.agents.map(agent =>
        agent.id === agentId ? { ...agent, ...update } : agent
      )
    };
  });
}
```

#### 4.5 API Integration Cleanup

Remove mock data and simulation code:

```typescript
// Before (simulation code):
function simulateWorkflowStep() {
  // Simulation logic...
}

// After (real API integration):
async function fetchTaskStatus(taskId: string) {
  try {
    const response = await api.getTaskStatus(taskId);
    return response.data;
  } catch (error) {
    console.error('Error fetching task status:', error);
    throw error;
  }
}
```

### Phase 5: Unused Code Cleanup (15 minutes)

Review and safely remove unused utility files and components.

#### Files to Check

1. **`/src/utils/input_processor.py`** - Check if used anywhere
2. **`/src/utils/create_test_audio.py`** - Keep only if used in tests
3. **`/src/components/Process/`** - Check if any unused components

#### Safety Check Commands

```bash
# Check if input_processor is used
grep -r "input_processor" src/ --exclude-dir=__pycache__

# Check if create_test_audio is used
grep -r "create_test_audio" src/ --exclude-dir=__pycache__

# Check for unused imports
ruff check --select F401 src/
```

#### Deletion Commands (Only if safe)

```bash
# Only remove if grep shows no usage and user confirms
# rm src/utils/input_processor.py  # Only if not used
# rm src/utils/create_test_audio.py  # Only if not used in tests
```

### Phase 6: Testing Improvements

#### 6.1 Test Reliability

Fix flaky tests:

```python
# Before:
def test_websocket_connect_disconnect(client):
    # Direct WebSocket object comparison
    assert websocket in connection_manager.active_connections[task_id]

# After:
def test_websocket_connect_disconnect(client):
    # Check connection exists without direct object comparison
    assert task_id in connection_manager.active_connections
    assert len(connection_manager.active_connections[task_id]) > 0
```

#### 6.2 Test Coverage

Add tests for untested code paths:

1. Error handling scenarios
2. Edge cases
3. Performance-critical paths

#### 6.3 Complete Workflow Testing

**After each phase, run complete workflow test:**

```bash
# 1. Start backend
uvicorn src.main:app --reload &
BACKEND_PID=$!

# 2. Start frontend
cd podcast-digest-ui
npm run dev &
FRONTEND_PID=$!

# 3. Test full workflow
# - Navigate to frontend in browser
# - Submit a YouTube URL
# - Verify processing pipeline works
# - Check audio generation
# - Verify WebSocket updates

# 4. Clean up
kill $BACKEND_PID $FRONTEND_PID
```

### Phase 7: Code Quality Tools & Pre-commit Setup

#### 7.1 Pre-commit Hooks Setup

Python linting with `ruff`:

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "B", "I", "N", "PYI", "UP", "TID"]
ignore = []

[tool.ruff.isort]
known-first-party = ["src"]
```

TypeScript/JavaScript linting with ESLint:

```javascript
// eslint.config.mjs
export default [
  {
    extends: [
      'eslint:recommended',
      'plugin:@typescript-eslint/recommended',
      'plugin:react/recommended',
      'plugin:react-hooks/recommended',
      'next/core-web-vitals',
    ],
    plugins: ['@typescript-eslint', 'react', 'react-hooks'],
    rules: {
      // Custom rules
    },
  },
];
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: 'v0.1.5'
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

**Install pre-commit:**

```bash
pre-commit install
pre-commit run --all-files
```

#### 7.2 Final Configuration Files

Python formatting with `black`:

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ["py311"]
include = '\.pyi?$'
```

TypeScript/JavaScript formatting with Prettier:

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "printWidth": 100,
  "trailingComma": "es5"
}
```

**Python configuration consolidated in pyproject.toml:**

Set up pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: 'v0.1.5'
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

### Phase 8: Performance Optimization

#### 8.1 Backend Optimizations

Optimize database/storage operations:

```python
# Implement connection pooling, caching, or batch operations
# Example: Batch processing for multiple transcripts
async def process_batch(video_ids: list[str]) -> dict[str, Any]:
    tasks = [fetch_transcript(video_id) for video_id in video_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    processed_results = {}
    for video_id, result in zip(video_ids, results):
        if isinstance(result, Exception):
            processed_results[video_id] = {"success": False, "error": str(result)}
        else:
            processed_results[video_id] = {"success": True, "data": result}

    return processed_results
```

#### 8.2 Frontend Optimizations

Implement React performance optimizations:

```typescript
// Use React.memo for component memoization
const AgentCard = React.memo(({ agent }: { agent: Agent }) => {
  // Component implementation
});

// Use useCallback for stable function references
const handleSubmit = useCallback((e: React.FormEvent) => {
  e.preventDefault();
  // Handler logic
}, [dependencies]);

// Use useMemo for expensive calculations
const sortedAgents = useMemo(() => {
  return [...agents].sort((a, b) => a.name.localeCompare(b.name));
}, [agents]);
```

### Phase 9: Dependency Management

#### 9.1 Backend Dependencies

Update Python dependencies:

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = "^0.23.2"
pydantic = "^2.4.2"
pydantic-settings = "^2.0.3"
# Other dependencies with version constraints

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.2"
black = "^23.10.1"
ruff = "^0.1.5"
mypy = "^1.6.1"
# Other dev dependencies
```

#### 9.2 Frontend Dependencies

Update npm dependencies:

```json
// package.json
{
  "dependencies": {
    "next": "^14.0.3",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.8.4",
    "axios": "^1.6.2",
    // Other dependencies
  },
  "devDependencies": {
    "typescript": "^5.2.2",
    "eslint": "^8.54.0",
    "prettier": "^3.1.0",
    // Other dev dependencies
  }
}
```

## Implementation Timeline

| Phase | Duration | Tasks | Testing |
|-------|----------|-------|----------|
| Phase 1 | 30 min | Backend cleanup & simulation removal | Test API endpoints |
| Phase 2 | 2-3 hrs | Code quality (linting, Pydantic v2, types) | Run full test suite |
| Phase 3 | 30 min | API integration update | Test complete workflow |
| Phase 4 | 1-2 hrs | Frontend cleanup & linting | Test UI functionality |
| Phase 5 | 15 min | Remove unused code | Verify no broken imports |
| Phase 6 | 1 hr | Testing improvements | Run comprehensive tests |
| Phase 7 | 30 min | Pre-commit hooks & quality gates | Test commit process |
| Phase 8 | 1 hr | Performance optimization | Benchmark improvements |
| Phase 9 | 30 min | Dependency management | Test build & deployment |
| **Total** | **7-9 hrs** | **Complete cleanup** | **Full system verification** |

## Files Modified Summary

### Deleted Files (4+ files)
- `src/processing/pipeline_simulation_backup.py` - 601 lines
- `src/tools/summarization_tools.py` - ~50 lines
- `src/tools/synthesis_tools.py` - ~50 lines
- `src/utils/audio_placeholder.py` - ~30 lines
- Additional unused files (after safety checks)

### Created Files (2+ files)
- `src/runners/simple_pipeline.py` - ~150 lines
- `src/exceptions.py` - Custom exception hierarchy
- `.pre-commit-config.yaml` - Pre-commit configuration
- Additional configuration files

### Modified Files (5+ files)
- `src/api/v1/endpoints/tasks.py` - Import and function call changes
- `pyproject.toml` - Tool configuration
- All Python files - Pydantic v2 compatibility
- Frontend configuration files
- Test files - Reliability improvements

### Deprecated Files (1 file)
- `src/runners/pipeline_runner.py` - Remove after testing complete

## Net Result

- **-400+ lines of code** (significant reduction)
- **Same functionality** (no feature loss)
- **Cleaner architecture** (easier to maintain)
- **Better performance** (less complexity overhead)
- **Quality gates** (prevent future regressions)
- **Type safety** (fewer runtime errors)

## Definition of Done

The cleanup is complete when:

✅ All simulation files are deleted safely
✅ Pipeline runner is simplified to <150 lines
✅ Linting/formatting tools are set up and working
✅ Pydantic v2 compatibility issues are fixed
✅ Type annotations are improved
✅ All existing tests pass
✅ Complete workflow test passes
✅ API endpoints work identically to before
✅ Audio generation produces identical output
✅ WebSocket updates work properly
✅ Error handling works as expected
✅ Pre-commit hooks are installed and working
✅ Unused code is safely removed
✅ Code is reviewed and approved
✅ Documentation is updated if needed
✅ Changes are committed to version control

## Risk Mitigation

**Risk Level**: Low-Medium (systematic approach with testing)

### Safety Measures
1. **Small incremental changes** with testing after each step
2. **Safety checks** before deleting any files
3. **User confirmation** for uncertain deletions
4. **Git branches** for safe development
5. **Comprehensive testing** after each phase
6. **Rollback plan** if issues arise

### Testing Strategy
1. **Unit tests** after code changes
2. **Integration tests** after API changes
3. **End-to-end tests** after each phase
4. **Performance benchmarks** to prevent regression
5. **Manual testing** of critical workflows

## Considerations and Constraints

1. **Backward Compatibility**:
   - Ensure API changes maintain compatibility
   - Provide migration paths for breaking changes

2. **Testing Impact**:
   - Changes should not break existing tests
   - Update tests to match new patterns

3. **Documentation**:
   - Update documentation to reflect changes
   - Document new patterns and best practices

4. **Deployment Impact**:
   - Coordinate changes with deployment plans
   - Test changes in staging environment
