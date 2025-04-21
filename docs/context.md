# Podcast Digest Agent: Project Context & Specification

> **This document is the canonical context/specification for the Podcast Digest Agent project. Reference this as the source of truth for requirements and architecture.**

---

## 1. Introduction

The **Podcast Digest Agent** is an automated system designed to process multiple podcast episodes (sourced from YouTube), summarize their content, and generate a single, engaging audio digest mimicking a two-person conversational format. The primary goal is to save the user significant listening time while keeping them informed about key topics discussed across their selected podcasts.

- **Agent Orchestration:** Google Agent Development Kit (ADK)
- **Audio Generation:** Google Cloud Text-to-Speech (TTS) API

---

## 2. Project Goal

Create a fully automated Python application using Google ADK that:
- Takes a list of YouTube podcast URLs
- Processes them to generate a synthesized dialogue script summarizing key points
- Outputs a single audio file using Google Cloud TTS with two distinct voices

---

## 3. Core User Story (MVP)

> As a user, I want to provide a list of YouTube podcast URLs in a text file, run a single script, and automatically receive a single MP3/WAV audio file in a local directory, which contains a summary of those podcasts presented as a conversation between two distinct AI voices, so that I can quickly get the key takeaways without manual processing or listening to the full episodes.

---

## 4. Technical Specifications

- **Target Platform:** 
  - Local machine (macOS, Linux, Windows)
- **Language:** Python 3.9+
- **Core Framework:** Google Agent Development Kit (ADK)
- **Key APIs:**
  - Google Cloud Text-to-Speech API (v1)
  - Google Cloud Vertex AI API (for Gemini models via ADK)
- **Essential Libraries:**
  - `google-adk`
  - `google-cloud-texttospeech`
  - `google-cloud-aiplatform`
  - `youtube-transcript-api` (or equivalent)
  - `pydub` (for audio concatenation)
  - Standard libraries: `os`, `json`, `datetime`, etc.
- **Configuration:**
  - Input URLs: `youtube_links.txt` (one URL per line)
  - API Credentials: Google Cloud Application Default Credentials (ADC)
  - Output Directory: `./output_audio/`
  - (Optional) Log file path
- **Authentication:** Google Cloud ADC (or service account keys)

## 4.1 ADK Implementation Architecture

### 4.1.1 Directory Structure
```
src/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── transcript_fetcher.py
│   ├── summarizer.py
│   └── synthesizer.py
├── tools/
│   ├── __init__.py
│   ├── transcript_tools.py
│   ├── summarization_tools.py
│   └── synthesis_tools.py
├── sessions/
│   ├── __init__.py
│   └── session_manager.py
└── runners/
    ├── __init__.py
    └── pipeline_runner.py
```

### 4.1.2 Agent Architecture
- **Base Agent**
  - Common agent functionality
  - Model initialization ('gemini-2.0-flash-exp')
  - Session management
  - Tool registration

- **Specialized Agents**
  - TranscriptFetcher: YouTube transcript retrieval
  - SummarizerAgent: Content summarization
  - SynthesizerAgent: Dialogue generation

### 4.1.3 Tool Organization
- **Toolset Classes**
  - Proper tool registration
  - Documentation standards
  - Error handling

- **Tool Types**
  - Function Tools
  - Agents-as-Tools
  - Built-in Tools
  - Third-Party Tools

### 4.1.4 Session Management
- **Session Service**
  - State persistence
  - Error recovery
  - Pipeline orchestration

### 4.1.5 Pipeline Runner
- **Runner Implementation**
  - Session management
  - Error handling
  - Pipeline orchestration

## 5. Detailed Workflow & Requirements

### 5.1 Initialization & Configuration Loading ✅
- ✅ Locate and read `youtube_links.txt`
- ✅ Ensure `./output_audio/` exists (create if necessary)
- ✅ Initialize ADK components and Google Cloud clients
- ✅ Verify Google Cloud authentication (ADC); log warning if missing

### 5.2 Input Processing ✅
- ✅ Parse input file, create list of YouTube URLs
- ✅ Handle empty lines/formatting issues gracefully
- ✅ Implement ADK agent/tool for fetching transcripts (Agent defined, Tool function implemented and used directly in runner)
- ✅ For each URL, use `youtube-transcript-api` (or equivalent) to fetch English transcript
- ✅ Robust error handling: log errors, return `None` for failures, do not crash pipeline

### 5.3 Transcript Fetching (Agent/Tool: TranscriptFetcher) ✅
- ✅ Implement ADK agent/tool for fetching transcripts (Agent defined, Tool function implemented and used directly in runner)
- ✅ For each URL, use `youtube-transcript-api` (or equivalent) to fetch English transcript
- ✅ Robust error handling: log errors, return `None` for failures, do not crash pipeline
- ✅ Output: Map of URLs to transcript text (or failure indicator)

### 5.4 Summarization (Agent: SummarizerAgent) ⏳
- ✅ ADK agent defined (inherits BaseAgent)
- ✅ Core summarization logic (LLM interaction) refined (Structure implemented, error handling enhanced)
- ✅ Input: single transcript text (Agent expects this)
- ✅ Output: concise summary of key points/topics/conclusions (Agent yields this, structure tested)
- ✅ Integration: Agent is now called directly by the runner (replaces placeholder)

### 5.5 Dialogue Synthesis (Agent: SynthesizerAgent) ⏳
- ✅ ADK agent defined (inherits BaseAgent/LlmAgent)
- ✅ Core dialogue generation logic (LLM interaction) implemented and refined (Structure implemented, JSON handling, error handling)
- ✅ Input: list of summaries (Expected)
- ✅ Output: single, cohesive dialogue script (Expected, Agent yields this)
  - ✅ Structure: assign each line to "Speaker A" or "Speaker B" (Expected, Agent yields this)
  - ✅ Output format: machine-readable (e.g., Python list of dicts: `[{"speaker": "A", "line": "..."}, ...]`) (Expected, Agent yields this)
- ✅ Integration: Agent is now called directly by the runner (replaces placeholder)

### 5.6 Audio Generation (Agent/Tool: AudioGenerator) ✅
- ✅ ADK agent defined (inherits BaseAgent/LlmAgent)
- ✅ Tool function `generate_audio_segment_tool` implemented and used directly in runner
- ✅ Core agent logic (if different from tool) needs implementation (Deferring for now, tool used directly)
- ✅ Define two high-quality Google Cloud TTS voice configs (Done in `audio_tools.py`)
- ✅ For each line in dialogue script: (Done via tool in runner)
  - ✅ Identify speaker, select voice config (Done via tool in runner)
  - ✅ Call TTS API with line text, voice config, audio encoding (MP3 or LINEAR16) (Done via tool in runner - async)
  - ✅ Handle TTS API errors gracefully (Done via tool in runner)
  - ✅ Store audio data for each segment (Done via tool in runner - saves files)

### 5.7 Audio Concatenation ✅
- ✅ Tool function `combine_audio_segments_tool` implemented and used directly in runner
- ✅ Use `pydub` (or similar) (Done via tool in runner)
- ✅ Load all audio segments in order (Done via tool in runner)
- ✅ Concatenate into single audio object (Done via tool in runner - async wrapper)
- ✅ Export to final format (MP3 recommended, WAV/LINEAR16 for processing) (Done via tool in runner)

### 5.8 Output Handling ✅
- ✅ Generate unique filename with timestamp (Done via tool in runner)
- ✅ Save final audio file to `./output_audio/` (Done via tool in runner)
- ✅ Handle file writing errors (Basic error handling in tool)

### 5.9 Logging & Error Reporting ✅
- ✅ Use Python `logging` module
- ✅ Log key events: pipeline start/end, config read, URLs found, transcript fetch success/failure, summary/synthesis/audio generation, file save
- ✅ Log errors at each major step

### 5.10 Testing ✅
- ✅ Update test organization
- ⏳ Add session tests (Relevant if session management is added)
- ✅ Add toolset tests (Basic tool tests exist, audio/transcript, refined)
- ✅ Add agent init tests (Implemented and fixed)
- ✅ Add pipeline runner tests (Implemented and fixed)
- ⏳ Add specific agent functionality tests (Summarizer basic structure tested w/ mocks, Synthesizer needed)

---

## 6. Implementation Phases

### Phase 1: Core Infrastructure ✅
1. **Directory Structure** ✅
   - Implement new directory structure
   - Create base classes
   - Update documentation

2. **Base Agent Implementation** ⏳
   - ✅ Create base agent with common functionality
   - ✅ Implement model initialization
   - ⏳ Implement core LLM interaction (`run` method - Basic implementation done, needs tool handling/error handling refinement)
   - ⏳ Add session management

3. **Toolset Implementation** ✅
   - Create toolset classes
   - Implement tool registration
   - Add documentation

### Phase 2: Agent Updates ⏳
1. **TranscriptFetcher Updates** ✅
   - Convert to proper ADK structure
   - Implement tool registration
   - Add session management (Agent defined, Tool function implemented)

2. **SummarizerAgent Implementation** ⏳
   - ✅ Create new agent
   - ✅ Implement Gemini integration / Core logic (Implemented, error handling enhanced)
   - ⏳ Add summarization tools (If needed beyond core agent logic)

3. **SynthesizerAgent Implementation** ⏳
   - ✅ Create new agent
   - ✅ Implement dialogue generation / Core logic (Implemented, JSON handling, error handling enhanced)
   - ⏳ Add synthesis tools (If needed beyond core agent logic)
   
4. **AudioGenerator Implementation** ✅
   - ✅ Create new agent
   - ✅ Implement audio tools (`generate_audio_segment_tool`, `combine_audio_segments_tool` - async)
   - ⏳ Core agent logic (If needed beyond tool functions - Deferred for now)

### Phase 3: Pipeline Integration ✅
1. **Runner Implementation** ✅
   - ✅ Create pipeline runner
   - ✅ Implement orchestration logic (using direct agent/tool calls)
   - ⏳ Implement session management (Not yet implemented in runner)
   - ✅ Add error handling

2. **Main Script Updates** ✅
   - ✅ Update main script
   - ✅ Implement initialization
   - ✅ Add pipeline orchestration

### Phase 4: Testing & Documentation ⏳
1. **Test Updates** ✅
   - ✅ Update test organization
   - ⏳ Add session tests (Relevant if session management is added)
   - ✅ Add toolset tests (Basic tool tests exist, audio/transcript, refined)
   - ✅ Add agent init tests (Implemented and fixed)
   - ✅ Add pipeline runner tests (Implemented and fixed)
   - ⏳ Add specific agent functionality tests (Summarizer/Synthesizer basic structure tested w/ mocks)

2. **Documentation Updates** ⏳
   - Update architecture diagrams
   - Add ADK specifics
   - Update setup instructions

---

## 7. Acceptance Criteria (MVP)

- Runs from command line via Python script
- Reads URLs from `youtube_links.txt`
- Fetches transcripts for >80% of test URLs with English captions
- Generates summaries and dialogue script without crashing
- Calls Google Cloud TTS API and generates audio segments
- Produces single, playable MP3/WAV file in `./output_audio/`
- Final audio alternates between two TTS voices
- Errors in transcript fetching for individual URLs do not stop processing of others
- Basic logs produced

---

## 8. Implementation Notes/Guidance

- **Start Simple:** Get core ADK structure, transcript fetching, and summarization working first
- **ADK Structure:** Use separate agents for Fetch, Summarize, Synthesize, GenerateAudio
- **LLM Prompting:** Expect to iterate on prompts for SummarizerAgent and SynthesizerAgent
- **Authentication:** Ensure `gcloud auth application-default login` is run before script
- **Dependency Management:** Use `requirements.txt` and consider `venv`
- **Error Handling:** Wrap external API calls in try/except
- **Audio Library:** `pydub` may require `ffmpeg` installed

---

## 9. Out of Scope (MVP Reminder)

- Focus on core, automated pipeline
- Do not add cloud storage, other input sources, or GUIs initially

---

## 10. Future Enhancements

- Cloud storage output (GCS)
- Support for audio file inputs + Cloud Speech-to-Text
- Parameterization/configuration of prompts, voices, output format
- Web UI or API endpoint
- More robust error handling and retries

---

## 11. V2 Requirements: API, Frontend, and Enhanced TTS

This section outlines planned enhancements for Version 2 of the Podcast Digest Agent, focusing on improved usability, integration capabilities, and audio quality.

### 11.1 Goal

To transform the command-line application into a web-accessible service with a user-friendly interface and leverage advanced multi-speaker TTS for more natural-sounding dialogue.

### 11.2 Core User Story (V2)

> As a user, I want to access a web page, paste a list of YouTube podcast URLs into a form, click a button to start processing, see the status of the generation, and finally listen to the generated conversational audio digest directly on the web page, so that I can easily create and consume podcast summaries without needing to run command-line scripts or manage local files.

### 11.3 Key Enhancements

#### 11.3.1 Google Cloud Speech Studio - Multi-Speaker TTS Integration

- **Requirement:** Replace the current Google Cloud Text-to-Speech API implementation (`texttospeech.TextToSpeechClient`) with Google Cloud Speech Studio's multi-speaker TTS capabilities.
- **Objective:** Achieve a more natural and consistent conversational flow by utilizing a single model trained or configured to produce distinct voices for Speaker A and Speaker B.
- **Impact:**
    - Requires investigation into Speech Studio API specifics (potentially different client libraries or REST API calls).
    - Voice configuration (`DEFAULT_VOICE_CONFIG` in `audio_tools.py`) will need significant changes. May involve referencing pre-trained studio voices or custom voice models.
    - The `synthesize_speech_segment` function and potentially the `GenerateAudioSegmentTool` will need refactoring to accommodate the new API/methodology.
    - Need to manage potential costs associated with Speech Studio usage.

#### 11.3.2 REST API Layer

- **Requirement:** Implement a RESTful API to expose the core agent pipeline functionality.
- **Objective:** Decouple the processing logic from direct user interaction, enabling integration with various clients (like the planned frontend) and potentially other systems.
- **Technology Suggestion:** FastAPI (due to its async nature, performance, and ease of use). Flask is also an option.
- **Key Endpoints:**
    - `POST /api/v1/digest`:
        - Input: `{"urls": ["url1", "url2", ...]}`
        - Action: Initiates the full podcast digest pipeline (transcript fetching, summarization, synthesis, audio generation).
        - Response: `{"job_id": "some_unique_id", "status": "pending"}` (Handles processing asynchronously).
    - `GET /api/v1/digest/status/{job_id}`:
        - Input: `job_id` from the POST request.
        - Action: Checks the status of the processing job.
        - Response: `{"job_id": "...", "status": "pending|processing|completed|failed", "message": "optional status message/error"}`
    - `GET /api/v1/digest/result/{job_id}`:
        - Input: `job_id`
        - Action: Retrieves the final audio file if the job is `completed`.
        - Response: The MP3 audio file directly (e.g., `Content-Type: audio/mpeg`) or a JSON response with a link/path `{"job_id": "...", "status": "completed", "audio_url": "/path/or/link/to/audio.mp3"}`. Needs decision on serving strategy.
- **Implementation:**
    - The API server will orchestrate calls to the existing agents/tools (likely via the `pipeline_runner` or a similar coordinator).
    - Requires managing job states (e.g., in-memory dictionary for simplicity, database for persistence).
    - Needs robust error handling for API requests and pipeline failures.

#### 11.3.3 Web Frontend

- **Requirement:** Develop a simple web-based user interface.
- **Objective:** Provide an accessible way for users to interact with the agent without using the command line.
- **Technology Suggestion:** Standard HTML, CSS, JavaScript. A lightweight framework like Vue.js, React, or Svelte could be used but is not strictly necessary for a basic MVP.
- **Key Features:**
    - **Input Form:** A text area for users to paste YouTube URLs (one per line).
    - **Submit Button:** To trigger the processing via the `POST /api/v1/digest` endpoint.
    - **Status Display:** Shows the current status of the job (polling `GET /api/v1/digest/status/{job_id}`).
    - **Audio Player:** An HTML5 `<audio>` element that becomes available and populated (using `GET /api/v1/digest/result/{job_id}`) once the job is complete.
    - **Error Handling:** Display user-friendly error messages if the API calls or processing fail.
- **Interaction:** The frontend will communicate exclusively with the REST API.

### 11.4 Updated Technical Specifications (Additions for V2)

- **API Framework:** FastAPI (recommended) or Flask
- **Frontend:** HTML, CSS, JavaScript (potential for React/Vue/Svelte)
- **TTS Engine:** Google Cloud Speech Studio (Multi-Speaker)
- **Job State Management:** In-memory (initially) or Database (e.g., SQLite, Redis)

### 11.5 Updated Workflow (Incorporating API/Frontend)

1.  **User Interaction:** User accesses the web frontend, pastes URLs, and clicks "Submit".
2.  **Frontend Request:** Frontend sends `POST /api/v1/digest` request to the backend API with the URLs.
3.  **API Processing:**
    - API receives request, validates input.
    - Generates a unique `job_id`.
    - Stores job state (e.g., `job_id`, `status: pending`).
    - Asynchronously triggers the `pipeline_runner` (or equivalent) with the URLs.
    - Returns `{"job_id": "...", "status": "pending"}` to the frontend.
4.  **Pipeline Execution (Async):** The existing pipeline runs (transcript, summary, synthesis, V2 audio generation). Job status is updated (`processing`, `completed`/`failed`). Audio file is saved (accessible by the API).
5.  **Frontend Polling:** Frontend periodically polls `GET /api/v1/digest/status/{job_id}` to update the displayed status.
6.  **Result Retrieval:** Once status is `completed`, the frontend enables the audio player and fetches the audio data via `GET /api/v1/digest/result/{job_id}`.
7.  **Playback:** User plays the audio digest directly in the browser.

### 11.6 Implementation Phases (Additions for V2)

- **Phase 5: TTS Migration**
    - Research and integrate Speech Studio Multi-Speaker TTS.
    - Refactor `audio_tools.py` and dependent components.
    - Update voice configurations.
    - Test audio generation quality.
- **Phase 6: REST API Development**
    - Set up FastAPI/Flask project structure.
    - Implement API endpoints (`/digest`, `/status`, `/result`).
    - Integrate API with the existing agent pipeline runner.
    - Implement job state management.
    - Add API-level error handling and validation.
- **Phase 7: Frontend Development**
    - Create basic HTML structure, CSS styling.
    - Implement JavaScript for API interaction (POSTing URLs, polling status, fetching/playing audio).
    - Develop UI components (form, button, status indicator, audio player).
- **Phase 8: Integration Testing & Deployment**
    - Test end-to-end flow (Frontend -> API -> Pipeline -> Audio Result).
    - Refine error handling and user feedback.
    - Document API usage and frontend operation.
    - Consider deployment strategy (e.g., running API server locally, containerization).

### 11.7 Acceptance Criteria (V2)

- User can submit URLs via the web frontend.
- Backend API successfully triggers the agent pipeline.
- Job status is correctly reported via the API and displayed on the frontend.
- Final audio digest is generated using Google Cloud Speech Studio Multi-Speaker TTS.
- Completed audio digest is playable directly on the web frontend.
- Basic error conditions (invalid URL, pipeline failure) are communicated to the user via the frontend.
- The system can handle at least one request at a time (concurrent requests are a future enhancement).

---

## 12. Code Quality and Refactoring Initiative

This section outlines a continuous initiative for maintaining and improving the overall quality, readability, maintainability, and robustness of the Podcast Digest Agent codebase.

### 12.1 Goal

To proactively manage technical debt, ensure adherence to best practices, and make the codebase easier to understand, test, and extend over time.

### 12.2 Scope & Focus Areas

This initiative covers the entire Python codebase (`src/`) and associated test files (`tests/`). Key areas of focus include:

1.  **Code Style & Formatting:**
    - **Requirement:** Enforce consistent code style.
    - **Tooling:** Utilize `black` for automated code formatting and `flake8` (with relevant plugins like `flake8-bugbear`, `flake8-annotations`) for linting.
    - **Action:** Configure linters/formatters and integrate them into the development workflow (e.g., pre-commit hooks, CI checks). Address all reported violations.

2.  **Docstrings & Typing:**
    - **Requirement:** Ensure all public modules, classes, functions, and methods have clear, concise docstrings (e.g., Google style).
    - **Requirement:** Maximize the use of Python type hints for function signatures and variables.
    - **Action:** Review and augment existing docstrings and type hints. Use tools like `mypy` for static type checking.

3.  **Code Complexity & Readability:**
    - **Requirement:** Simplify overly complex functions or classes.
    - **Action:** Refactor long methods, reduce nesting levels, improve variable naming, and enhance overall logical flow.

4.  **Error Handling:**
    - **Requirement:** Ensure consistent and robust error handling, especially around external API calls, file I/O, and data validation.
    - **Action:** Use specific exception types where possible, provide informative log messages, and ensure failures are handled gracefully without crashing the application unnecessarily.

5.  **Testing:**
    - **Requirement:** Increase test coverage, particularly for critical logic, edge cases, and error paths.
    - **Action:** Write new unit and integration tests using `pytest`. Refactor existing tests for clarity and efficiency. Ensure tests are reliable and run quickly.

6.  **Dependency Management:**
    - **Requirement:** Keep dependencies (`requirements.txt`) up-to-date and remove unused ones.
    - **Action:** Regularly review dependencies for security vulnerabilities and updates. Ensure version pinning is used appropriately.

7.  **Dead Code Removal:**
    - **Requirement:** Identify and remove any unused variables, functions, classes, or imports.
    - **Action:** Use static analysis tools or manual review to find and eliminate dead code.

8.  **Performance:**
    - **Requirement:** Identify and address performance bottlenecks where applicable (e.g., inefficient loops, blocking I/O in async code).
    - **Action:** Profile code sections if performance issues are suspected. Optimize critical paths without sacrificing readability.

### 12.3 Process

- Code quality improvements should be an ongoing effort, integrated into regular development sprints or feature work.
- Consider dedicated refactoring sprints or tasks if significant technical debt accumulates.
- All new code contributions must adhere to the established quality standards (linting, formatting, typing, testing).
- Code reviews should explicitly check for adherence to these quality standards.

### 12.4 Acceptance Criteria

- Codebase consistently passes `black`, `flake8`, and `mypy` checks without errors.
- Test coverage meets a defined target (e.g., >85% line coverage for core modules).
- Docstrings and type hints are present and accurate for all major components.
- Key complex areas identified during reviews have been refactored.
- No known dead code remains in the main branches.
- Dependencies are reviewed and updated.

---
