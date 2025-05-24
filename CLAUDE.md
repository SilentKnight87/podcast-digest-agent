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
- Make small incremental changes and test thoroughly after each step when implementing a feature

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

[Rest of the file remains unchanged...]
