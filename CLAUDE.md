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
- Always update existing tests or create new ones and run them once a feature is completed
- **Testing Protocol**: After implementing any feature:
  1. Update all tests within scope to match the new implementation
  2. Run the tests using pytest
  3. Fix any failing tests and iterate until all pass
  4. Consider adding new tests for edge cases discovered during implementation
  5. **Important**: Mock at the correct API level - if the implementation uses `list_transcripts()`, don't mock `get_transcript()`
  6. **Important**: Use realistic mock data that matches the actual API response format (objects vs dictionaries)
- **Feature Documentation**: After completing a feature:
  1. Update the corresponding spec document in `/specs/` directory
  2. Add a standardized status section at the top of the spec showing completion status
  3. Document any deviations from the original spec and reasons for changes

### Spec Status Format Template
```markdown
## Status: [STATUS_EMOJI] [STATUS_TEXT]

**Completion Date**: [Date if completed]
**Priority**: [High/Medium/Low]
**Estimated Time**: [Time estimate]
**Actual Time**: [Actual time if completed]
**Dependencies**: [List any dependencies]

### Implementation Summary (if completed)
- ✅ [Completed task 1]
- ✅ [Completed task 2]
- ☐ [Incomplete task if any]

### Deviations from Original Spec (if any)
- [List any changes made during implementation]
```

Status Options:
- ✅ COMPLETED
- 🚀 IN PROGRESS
- 📝 NOT STARTED
- ⚠️ BLOCKED
- ❌ CANCELLED

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

**Completed Cleanup**:
- `BACKEND_CLEANUP_PRD.md`: ✅ COMPLETED - Removed 730+ lines of simulation code, simplified pipeline runner from 467 to 171 lines

**Recent Bug Fixes**:
- Fixed YouTube transcript API error due to API returning objects instead of dictionaries
- Updated tests to properly mock the new `list_transcripts()` API method
- Added fallback logic for different transcript types (manual → auto-generated → any language)

**Pending Features**:
- `GOOGLE_ADK_MIGRATION_PRD.md`: Future migration to Google ADK for learning

[... rest of the file remains unchanged ...]