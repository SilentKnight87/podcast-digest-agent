# Frontend-Backend Integration Implementation Plan

## Overview

This document outlines a detailed plan to complete the integration between the Next.js frontend and FastAPI backend of the Podcast Digest Agent. The current implementation has a frontend that uses mock data and a backend that originally processed YouTube URLs from a file (`input/youtube_links.txt`). This plan focuses on transitioning to a fully integrated system where the frontend submits YouTube URLs directly to the backend via API and receives real-time updates about processing status and results.

## Current State Assessment

### Frontend
- UI components are implemented (HeroSection, ProcessingVisualizer, PlayDigestButton)
- WorkflowContext manages state but uses mock data
- API client and WebSocket manager are implemented but need refinement
- Audio playback has basic implementation but needs connection to real backend data

### Backend
- API endpoints are defined and partially implemented
- Pipeline designed to read from `input/youtube_links.txt` rather than API input
- Agent modules implemented but need connection to the pipeline
- WebSocket broadcasting implemented in the task manager
- Audio generation works but file paths need standardization for web access

## Integration Goals

1. Modify the backend to process URLs from API requests rather than files
2. Ensure data passed between frontend and backend is consistently formatted
3. Implement proper error handling throughout the system
4. Configure consistent file paths and URL structures for audio files
5. Create a seamless user experience from URL submission to audio playback

## Implementation Plan

### Phase 1: Backend Pipeline Adaptation

1. **Update `run_processing_pipeline` in `pipeline.py`**
   - Modify to work directly with the provided URL from API request
   - Ensure it's already connected to the task management system

```python
# src/processing/pipeline.py - Key modifications

async def run_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """
    Process a YouTube URL through the pipeline of agents.
    This is run as a background task after the API request is accepted.
    """
    # Extract YouTube URL from request data
    youtube_url = request_data.youtube_url
    logger.info(f"Starting processing pipeline for URL: {youtube_url}, task ID: {task_id}")

    try:
        # Initialize pipeline with task status updates
        task_manager.update_task_processing_status(
            task_id,
            "processing",
            progress=5,
            current_agent_id="youtube-node"
        )

        # Process the URL directly instead of reading from file
        # Rest of the function remains similar, just working with the URL parameter
        # ...
```

2. **Ensure Audio File Access from Web**
   - Update audio file generation paths to be web-accessible
   - Update filename conventions to be consistent

```python
# In src/processing/pipeline.py - Audio file handling

# Create a real audio file using the AudioGenerator agent
audio_filename = f"{task_id}_digest.mp3"  # Consistent naming convention
output_audio_dir = Path(settings.OUTPUT_AUDIO_DIR)
output_audio_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

# Construct the URL for the audio file - make sure this is consistent
audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}"

# Save task completion with the correct audio URL
task_manager.set_task_completed(task_id, summary, audio_url)
```

3. **Add Robust Error Handling**
   - Improve exception handling throughout the pipeline
   - Ensure WebSocket clients are notified of errors

```python
# Error handling in pipeline.py

try:
    # Pipeline processing code
    # ...
except Exception as e:
    logger.error(f"Error in processing pipeline for task {task_id}: {e}", exc_info=True)
    # Update task with error status
    task_manager.set_task_failed(task_id, str(e))
    # Make sure error is propagated to frontend via WebSocket
```

### Phase 2: Audio Processing Enhancement

1. **Verify AudioGenerator Integration**
   - Ensure audio generation with Google Cloud TTS is working
   - Implement fallback options for development/testing

```python
# Validate the existing integration in audio_generator.py
# Ensure audio file paths are consistent
# Add more robust error handling

# Fallback audio generation if TTS fails
try:
    from src.utils.create_test_audio import create_test_wav
    audio_file_path = output_audio_dir / audio_filename
    create_test_wav(str(audio_file_path), duration_seconds=10.0)
    logger.info(f"Created fallback audio file: {audio_file_path}")
except Exception as fallback_error:
    logger.error(f"Failed even creating fallback audio: {fallback_error}")
```

### Phase 3: Frontend Integration Refinement

1. **Update `api-client.ts` and Type Definitions**
   - Ensure API client is correctly configured
   - Update type definitions to match backend Pydantic models

```typescript
// podcast-digest-ui/src/lib/api-client.ts
// Ensure the getAudioFile method creates the correct URL

getAudioFile: (audioFileName: string) => {
  // Ensure this correctly formats the URL to match backend
  // audioFileName should be just the filename, not the full path or URL
  if (!audioFileName) return '';

  // If it's already a full URL, return it
  if (audioFileName.startsWith('http')) return audioFileName;

  // If it's a path or filename, construct the URL
  const fileName = audioFileName.split('/').pop();
  return `${API_BASE_URL}/api/v1/audio/${fileName}`;
}
```

2. **Update `WorkflowContext.tsx` for Audio URL Handling**
   - Fix the mapping of backend audio_file_url to frontend outputUrl
   - Add debugging to track URL values

```typescript
// podcast-digest-ui/src/contexts/WorkflowContext.tsx
// Within mapApiResponseToWorkflowState function:

// Log the raw audio URL from backend
console.log('[WorkflowContext] Mapping API response:', {
  audio_file_url: response.audio_file_url,
  status: response.processing_status.status
});

const result = {
  // ... other mapped fields ...
  outputUrl: response.audio_file_url || undefined  // Make sure this is explicit
};

// Verify mapping result
console.log('[WorkflowContext] Mapped result:', {
  outputUrl: result.outputUrl,
  hasOutputUrl: !!result.outputUrl
});

return result;
```

3. **Fix `PlayDigestButton.tsx` Audio URL Handling**
   - Ensure it correctly retrieves and plays the audio URL

```typescript
// podcast-digest-ui/src/components/Hero/PlayDigestButton.tsx

// Debug the audio URL in the PlayDigestButton
useEffect(() => {
  console.log('[PlayDigestButton] Audio URL state:', {
    workflowOutputUrl: workflowState?.outputUrl,
    audioUrl: audioUrl,
    isAudioUrlSet: !!audioUrl
  });
}, [workflowState?.outputUrl, audioUrl]);

// Update the handlePlay function
const handlePlayClick = () => {
  if (workflowState?.outputUrl) {
    // Get and log the processed audio URL
    const processedUrl = api.getAudioFile(workflowState.outputUrl);
    console.log('[PlayDigestButton] Playing audio from URL:', processedUrl);

    setAudioUrl(processedUrl);

    // Rest of the play logic...
  } else {
    console.error('[PlayDigestButton] No audio URL available to play');
  }
};
```

### Phase 4: End-to-End Testing and Debugging

1. **Create a Testing Protocol**

```
Step 1: Start the backend server
  - Run: `uvicorn src.main:app --reload`
  - Verify the server starts without errors

Step 2: Start the frontend development server
  - Navigate to frontend directory: `cd podcast-digest-ui`
  - Run: `npm run dev`
  - Verify the website loads at http://localhost:3000

Step 3: Test the full flow
  - Enter a known working YouTube URL: https://www.youtube.com/watch?v=NnFVDWQQUCw
  - Submit the URL and observe the processing visualization
  - Check the backend logs for any errors
  - Verify WebSocket messages in browser developer tools
  - Wait for processing to complete and test the audio playback
```

2. **Debugging Tools and Techniques**

```
Backend Debugging:
- Add detailed logging at each stage of the pipeline
- Log input/output data of each agent
- Track WebSocket message sending

Frontend Debugging:
- Use browser developer tools to monitor:
  - Network requests (API calls and WebSocket)
  - Console logs from the integration points
  - React component rendering

Audio File Debugging:
- Verify file exists on disk
- Check file permissions
- Test direct file URL access in browser
```

## Implementation Details

### 1. Fix Pipeline to Use API Request URL

First, we'll modify the pipeline to use the URL from the API request rather than reading from a file.

```python
# Current implementation that needs to be modified
# src/processing/pipeline.py

async def run_processing_pipeline(task_id: str, request_data: ProcessUrlRequest):
    """
    Process a YouTube URL through the pipeline of agents.
    This is run as a background task after the API request is accepted.
    """
    youtube_url = request_data.youtube_url
    logger.info(f"Processing YouTube URL: {youtube_url}, task ID: {task_id}")

    # Use the URL directly in agent calls instead of reading from file
    # For example, in transcript fetching:
    transcript = await transcript_fetcher.fetch_transcript(youtube_url)

    # Continue with the rest of the pipeline using the direct URL
    # ...
```

### 2. Audio File Path and URL Consistency

We need to ensure consistent file paths and URLs for audio files:

```python
# In src/processing/pipeline.py
# After audio generation is complete

# Get just the filename for the URL
audio_filename = Path(audio_file_path).name

# Construct the URL using settings
audio_url = f"{settings.API_V1_STR}/audio/{audio_filename}"

# Store this URL in the task completion data
task_manager.set_task_completed(task_id, summary, audio_url)
```

### 3. Frontend URL Handling

Fix the frontend to correctly process and use audio URLs:

```typescript
// In podcast-digest-ui/src/contexts/WorkflowContext.tsx
// Update in the mapping function

// Ensure we properly extract the audio URL
const audioUrl = response.audio_file_url || undefined;
console.log(`[Mapping] Audio URL from API: ${audioUrl}`);

return {
  // ... other mapped fields ...
  outputUrl: audioUrl
};
```

## Verification Steps

After implementing the changes, use this checklist to verify the integration:

1. **API Request**
   - [ ] Frontend submits YouTube URL to backend
   - [ ] Backend accepts the URL and creates a task
   - [ ] Frontend receives task ID and connects WebSocket

2. **Processing Pipeline**
   - [ ] Pipeline processes the URL directly
   - [ ] Agent status updates are broadcast via WebSocket
   - [ ] Frontend visualization shows real-time updates

3. **Audio Output**
   - [ ] Audio file is generated with correct name
   - [ ] Audio URL is properly formatted
   - [ ] Frontend receives and processes the URL correctly
   - [ ] Audio plays successfully in the frontend

4. **Error Handling**
   - [ ] Invalid URLs are rejected with helpful messages
   - [ ] Pipeline errors are communicated to the frontend
   - [ ] Graceful fallbacks are used when possible

## Troubleshooting Guide

If integration issues occur, here's how to diagnose and fix them:

1. **WebSocket Connection Issues**
   - Check CORS settings in the backend
   - Verify WebSocket URL formatting in the frontend
   - Make sure proper error handling is in place

2. **Audio Playback Issues**
   - Verify the audio file exists on the server
   - Check the URL formatting in both backend and frontend
   - Test the audio endpoint directly in the browser
   - Check browser console for media errors

3. **Pipeline Processing Issues**
   - Look for errors in the backend logs
   - Verify each agent is initialized properly
   - Make sure exception handling captures and reports issues

## Conclusion

This implementation plan provides a detailed roadmap to complete the integration between the frontend and backend of the Podcast Digest Agent. By addressing the specific challenges of transitioning from file-based to API-based processing and ensuring consistent data flow between components, we can create a seamless user experience from URL submission to audio playback.

The plan focuses on practical changes to specific files and functions, with clear verification steps and troubleshooting guidance. Following this plan will enable the successful completion of the integration and bring the application to a fully functional state.
