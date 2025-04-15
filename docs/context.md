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
  - Docker container (for consistent deployment)
- **Language:** Python 3.9+
- **Core Framework:** Google Agent Development Kit (ADK)
- **Containerization:** Docker
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

## 4.1 Containerization Requirements

- **Base Image:** Python 3.9-slim
- **Volume Mounts:**
  - Input directory for `youtube_links.txt`
  - Output directory for generated audio files
- **Environment Variables:**
  - `GOOGLE_APPLICATION_CREDENTIALS` (optional, for service account)
  - `LOG_FILE` (optional, for persistent logging)
- **Dependencies:**
  - FFmpeg (required by pydub)
  - Python dependencies from requirements.txt
- **Build Context:**
  - Exclude virtual environments, cache files, and output directories
- **Runtime:**
  - Non-root user for security
  - Proper file permissions for mounted volumes

---

## 5. Detailed Workflow & Requirements

### 5.1 Initialization & Configuration Loading ✅
- Locate and read `youtube_links.txt`
- Ensure `./output_audio/` exists (create if necessary)
- Initialize ADK components and Google Cloud clients
- Verify Google Cloud authentication (ADC); log warning if missing

### 5.2 Input Processing ✅
- Parse input file, create list of YouTube URLs
- Handle empty lines/formatting issues gracefully

### 5.3 Transcript Fetching (Agent/Tool: TranscriptFetcher)
- Implement ADK agent/tool for fetching transcripts
- For each URL, use `youtube-transcript-api` (or equivalent) to fetch English transcript
- Robust error handling: log errors, return `None` for failures, do not crash pipeline
- Output: Map of URLs to transcript text (or failure indicator)
- File Structure Updates:
  ```
  podcast-digest-agent/
  ├── .env                    # Environment variables (API keys, config)
  ├── .gitignore             # Git ignore patterns (separate from .dockerignore)
  ├── .dockerignore          # Docker ignore patterns
  ├── README.md              # Project documentation
  ├── requirements.txt       # Python dependencies
  ├── Dockerfile             # Docker configuration
  ├── docker-compose.yml     # Docker compose configuration
  ├── src/                   # Source code
  │   ├── __init__.py
  │   ├── main.py           # Entry point
  │   ├── agents/           # ADK agents
  │   │   ├── __init__.py
  │   │   ├── transcript_fetcher.py
  │   │   ├── summarizer.py
  │   │   └── synthesizer.py
  │   ├── tools/            # ADK tools
  │   │   ├── __init__.py
  │   │   └── audio_generator.py
  │   ├── utils/            # Utility functions
  │   │   ├── __init__.py
  │   │   ├── input_processor.py
  │   │   └── logging.py
  │   └── config/           # Configuration files
  │       ├── __init__.py
  │       └── settings.py
  ├── tests/                # Test files
  │   ├── __init__.py
  │   ├── test_main.py
  │   ├── test_input_processor.py
  │   └── test_agents/
  │       ├── __init__.py
  │       └── test_transcript_fetcher.py
  ├── input/                # Input files
  │   └── youtube_links.txt
  └── output_audio/         # Output directory
  ```
  - `.gitignore` needed despite `.dockerignore`:
    - `.gitignore` handles version control (e.g., IDE files, Python cache)
    - `.dockerignore` handles Docker build context (e.g., virtual environments, large files)
    - Both serve different purposes and should be maintained separately

### 5.4 Summarization (Agent: SummarizerAgent)
- ADK agent using LLM (Gemini via Vertex AI)
- Input: single transcript text
- Output: concise summary of key points/topics/conclusions

### 5.5 Dialogue Synthesis (Agent: SynthesizerAgent)
- ADK agent using LLM (Gemini via Vertex AI)
- Input: list of summaries
- Output: single, cohesive dialogue script
  - Structure: assign each line to "Speaker A" or "Speaker B"
  - Output format: machine-readable (e.g., Python list of dicts: `[{"speaker": "A", "line": "..."}, ...]`)

### 5.6 Audio Generation (Agent/Tool: AudioGenerator)
- ADK agent/tool for TTS generation
- Define two high-quality Google Cloud TTS voice configs (e.g., en-US-Wavenet-D for A, en-US-Wavenet-F for B)
- For each line in dialogue script:
  - Identify speaker, select voice config
  - Call TTS API with line text, voice config, audio encoding (MP3 or LINEAR16)
  - Handle TTS API errors gracefully
  - Store audio data for each segment (in-memory or temp files)

### 5.7 Audio Concatenation
- Use `pydub` (or similar)
- Load all audio segments in order
- Concatenate into single audio object
- Export to final format (MP3 recommended, WAV/LINEAR16 for processing)

### 5.8 Output Handling
- Generate unique filename with timestamp (e.g., `podcast_digest_YYYYMMDD_HHMMSS.mp3`)
- Save final audio file to `./output_audio/`
- Handle file writing errors

### 5.9 Logging & Error Reporting
- Use Python `logging` module
- Log key events: pipeline start/end, config read, URLs found, transcript fetch success/failure, summary/synthesis/audio generation, file save
- Log errors at each major step

---

## Testing & Verification

### 5.1 Initialization & Configuration Loading
- Output directory is created if missing
- Input file is read correctly (including missing/empty file)
- Logging occurs for missing input file
- ADC check logs warning if credentials are missing (mock os.environ and os.path.exists)
- Client initialization stub logs info

### 5.2 Input Processing
- Handles empty lines and malformed URLs gracefully
- Returns a clean list of valid YouTube URLs
- Logs and skips invalid lines

### 5.3 Transcript Fetching (TranscriptFetcher)
- Fetches transcript for valid YouTube URLs
- Handles unavailable/private videos or missing transcripts without crashing
- Logs errors for failed fetches
- Returns None or error indicator for failed URLs

### 5.4 Summarization (SummarizerAgent)
- Produces concise summary for valid transcript input
- Handles empty or malformed transcript input gracefully
- Logs and skips on LLM/API errors

### 5.5 Dialogue Synthesis (SynthesizerAgent)
- Produces a structured dialogue script from summaries
- Ensures output alternates between two speakers
- Output is machine-readable (list of dicts)
- Handles empty or malformed summaries gracefully

### 5.6 Audio Generation (AudioGenerator)
- Generates audio segments for each dialogue line
- Uses correct TTS voice for each speaker
- Handles TTS API errors gracefully (logs/skips as needed)
- Stores audio segments in correct order

### 5.7 Audio Concatenation
- Concatenates all audio segments in correct order
- Produces a single audio object/file
- Handles missing/corrupt segments gracefully

### 5.8 Output Handling
- Generates unique filename with timestamp
- Saves final audio file to output directory
- Handles file I/O errors gracefully

### 5.9 Logging & Error Reporting
- Logs all key events and errors at each pipeline step
- Log file (if configured) is created and written to
- Errors in one step do not prevent processing of other valid items

---

## 6. Acceptance Criteria (MVP)

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

## 7. Implementation Notes/Guidance

- **Start Simple:** Get core ADK structure, transcript fetching, and summarization working first
- **ADK Structure:** Use separate agents for Fetch, Summarize, Synthesize, GenerateAudio
- **LLM Prompting:** Expect to iterate on prompts for SummarizerAgent and SynthesizerAgent
- **Authentication:** Ensure `gcloud auth application-default login` is run before script
- **Dependency Management:** Use `requirements.txt` and consider `venv`
- **Error Handling:** Wrap external API calls in try/except
- **Audio Library:** `pydub` may require `ffmpeg` installed

---

## 8. Out of Scope (MVP Reminder)

- Focus on core, automated pipeline
- Do not add cloud storage, other input sources, or GUIs initially

---

## 9. Future Enhancements

- Cloud storage output (GCS)
- Support for audio file inputs + Cloud Speech-to-Text
- Parameterization/configuration of prompts, voices, output format
- Web UI or API endpoint
- More robust error handling and retries
