# Test Status Report

## Overview

This document provides a summary of the test status for the Podcast Digest Agent project as of May 18, 2025.

## Core Tests Status

All critical functionality tests are passing:

- ✅ Agent tests (`tests/agents/`) 
- ✅ API v1 tests (`tests/api/test_api_v1.py`)
- ✅ Main HTTP API tests (`tests/api/test_main_http_api.py`)

## Known Issues

### WebSocket Tests

All WebSocket-related tests have been skipped due to known issues with WebSocket testing in the test client:

- ⚠️ The `WebSocketTestSession` object from `starlette.testclient` doesn't match the `WebSocket` object from FastAPI stored in the connection manager.
- ⚠️ This causes equality comparison to fail in tests like `test_websocket_connect_disconnect`.

The skipped tests are marked with appropriate messages in the test files:
- `tests/api/test_main_websocket_api.py`
- `tests/api/test_api_v1.py` (WebSocket-related tests)

### History API Tests

The history endpoint functionality is not fully implemented yet, so the following tests are skipped:

- `test_get_task_history_with_completed_tasks` in `tests/api/test_api_v1.py`
- Various tests in `tests/api/test_history_api.py`

### Settings Tests

The settings tests in `tests/config/test_settings.py` have some failures due to:

- Path resolution differences between test and production environments
- Directory creation behavior when running in a container vs. locally

### Other Test Failures

There are failures in the following test files that require further investigation:

- `tests/core/test_task_manager.py`
- `tests/models/test_api_models.py`
- `tests/test_agents.py`
- `tests/test_pipeline_integration.py`
- `tests/test_pipeline_runner.py`
- `tests/test_transcript_tools.py`

## Deprecation Warnings

The codebase has several deprecation warnings that should be addressed in future updates:

1. Pydantic V2 Compatibility:
   - Replace `.dict()` with `.model_dump()` throughout the codebase
   - Update Field extra keywords to use `json_schema_extra`
   - Replace class-based `config` with `ConfigDict`

2. pytest-asyncio Configuration:
   - Set the `asyncio_default_fixture_loop_scope` configuration option

3. Asyncio Tests:
   - Some tests marked with `@pytest.mark.asyncio` are not async functions

## Next Steps

1. **High Priority**: Investigate and fix the task manager test failures
2. **Medium Priority**: Update Pydantic usage to eliminate deprecation warnings
3. **Medium Priority**: Fix settings tests to work properly in all environments
4. **Low Priority**: Implement history API functionality to enable skipped tests
5. **Low Priority**: Enhance WebSocket testing approach or create a testing utility for WebSockets

## Running Tests

To run the core tests that are known to pass:

```bash
pytest tests/agents/ tests/api/test_api_v1.py tests/api/test_main_http_api.py
```

To run all tests (including those that are known to fail):

```bash
pytest
```

To run specific test files:

```bash
pytest tests/path/to/test_file.py
```

To run specific test functions:

```bash
pytest tests/path/to/test_file.py::test_function_name
```