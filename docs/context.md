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
