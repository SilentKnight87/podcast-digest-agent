# Code Cleanup Specification

## Overview

This specification outlines the plan for cleaning up the Podcast Digest Agent codebase to prepare it for deployment. The cleanup will focus on addressing technical debt, improving code quality, standardizing patterns, and optimizing performance.

## Goals

1. Standardize code formatting and style across the codebase
2. Resolve deprecation warnings and technical debt
3. Improve type safety and error handling
4. Optimize performance and resource usage
5. Remove unused code and dependencies
6. Ensure consistent code patterns and architecture
7. Implement code quality gates and linting

## Implementation Details

### 1. Backend (Python) Code Cleanup

#### 1.1 Fix Pydantic V2 Compatibility Issues

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

#### 1.2 Type Annotations and Validation

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

#### 1.3 Error Handling Improvements

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

#### 1.4 Code Organization and Structure

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

#### 1.5 Configuration Management

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

### 2. Frontend (Next.js) Code Cleanup

#### 2.1 Component Organization

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

#### 2.2 TypeScript Improvements

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

#### 2.3 State Management Refactoring

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

#### 2.4 API Integration Cleanup

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

### 3. Testing Improvements

#### 3.1 Test Reliability

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

#### 3.2 Test Coverage

Add tests for untested code paths:

1. Error handling scenarios
2. Edge cases
3. Performance-critical paths

### 4. Code Quality Tools

#### 4.1 Linting Configuration

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

#### 4.2 Formatting Configuration

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

#### 4.3 Pre-commit Hooks

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

### 5. Performance Optimization

#### 5.1 Backend Optimizations

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

#### 5.2 Frontend Optimizations

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

### 6. Dependency Management

#### 6.1 Backend Dependencies

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

#### 6.2 Frontend Dependencies

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

## Implementation Plan

### Phase 1: Code Formatting and Style

1. Set up linting and formatting tools
2. Apply automated fixes for consistent style
3. Address manual formatting issues
4. Implement pre-commit hooks

### Phase 2: Technical Debt Resolution

1. Fix Pydantic V2 compatibility issues
2. Update deprecated method calls
3. Implement proper type annotations
4. Clean up error handling patterns

### Phase 3: Optimization and Testing

1. Optimize performance-critical paths
2. Fix flaky tests
3. Improve test coverage
4. Document performance improvements

### Phase 4: Architecture Improvements

1. Refactor code organization
2. Implement consistent patterns
3. Remove unused code
4. Streamline dependencies

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