# Backend Cleanup PRD

## Overview

This specification outlines a comprehensive cleanup plan for the podcast digest backend to remove simulation files, simplify the pipeline runner, and eliminate redundant code while maintaining full functionality.

## Goals

1. Remove simulation files and redundant code (601+ lines)
2. Simplify pipeline runner from 467 to ~100 lines
3. Maintain all existing functionality
4. Improve code maintainability and readability
5. Reduce memory usage and complexity
6. Preserve error handling and logging

## Implementation Details

### Phase 1: Remove Simulation Files (30 minutes)

The current backend has accumulated unnecessary simulation files that need to be removed.

#### Files to Delete Completely

1. **`/src/processing/pipeline_simulation_backup.py`** - 601 lines of pure simulation code
2. **`/src/tools/summarization_tools.py`** - Redundant with SummarizerAgent
3. **`/src/tools/synthesis_tools.py`** - Redundant with SynthesizerAgent  
4. **`/src/utils/audio_placeholder.py`** - Placeholder logic no longer needed

#### Commands to Execute

```bash
# Navigate to project root
cd /Users/peterbrown/Documents/Code/podcast-digest-agent

# Remove simulation files
rm src/processing/pipeline_simulation_backup.py
rm src/tools/summarization_tools.py
rm src/tools/synthesis_tools.py
rm src/utils/audio_placeholder.py

# Verify files are removed
ls -la src/processing/
ls -la src/tools/
ls -la src/utils/
```

### Phase 2: Simplify Pipeline Runner (2-3 hours)

The current pipeline runner is overly complex with 467 lines. We'll replace it with a simplified version.

#### Current Issues with `/src/runners/pipeline_runner.py`

- **467 lines** of overly complex orchestration
- Unnecessary helper methods and complex error handling
- Over-engineered result processing
- Complex temporary directory management

#### Create New Simplified Version

**New file**: `/src/runners/simple_pipeline.py`

```python
"""
Simplified Pipeline Runner for podcast digest generation.
"""
import logging
import asyncio
import tempfile
import shutil
import json
from typing import List, Dict
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
        self.temp_dirs = []
        logger.info("SimplePipeline initialized")

    async def run_async(self, video_ids: List[str], output_dir: str) -> Dict:
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

    def _extract_successful_transcripts(self, results: Dict) -> Dict[str, str]:
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

    async def _synthesize_dialogue(self, summaries: List[str]) -> List[Dict]:
        """Synthesize dialogue from summaries."""
        try:
            summaries_json = json.dumps(summaries)
            async for event in self.synthesizer.run_async(summaries_json):
                if event.type.name == "RESULT" and "dialogue" in event.payload:
                    return event.payload["dialogue"]
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
        return []

    async def _generate_audio(self, dialogue: List[Dict], output_dir: str, tts_client) -> str:
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

    def _error_result(self, error_msg: str, video_ids: List[str]) -> Dict:
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

    def _cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Cleanup failed for {temp_dir}: {e}")
        self.temp_dirs.clear()

    def run_pipeline(self, video_ids: List[str], output_dir: str = "./output_audio") -> Dict:
        """Synchronous wrapper for async pipeline."""
        return asyncio.run(self.run_async(video_ids, output_dir))
```

### Phase 3: Update API Integration (30 minutes)

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

### Phase 4: Clean Up Unused Utilities (15 minutes)

Review and potentially remove unused utility files.

#### Files to Check

1. **`/src/utils/input_processor.py`** - Check if used anywhere
2. **`/src/utils/create_test_audio.py`** - Keep only if used in tests

#### Commands to Check Usage

```bash
# Check if input_processor is used
grep -r "input_processor" src/ --exclude-dir=__pycache__

# Check if create_test_audio is used
grep -r "create_test_audio" src/ --exclude-dir=__pycache__

# If not used, remove them
# rm src/utils/input_processor.py  # Only if not used
# rm src/utils/create_test_audio.py  # Only if not used in tests
```

### Phase 5: Testing and Verification (30 minutes)

Thoroughly test the simplified pipeline to ensure all functionality is preserved.

#### Manual Testing Steps

1. **Start the backend server**
   ```bash
   cd /Users/peterbrown/Documents/Code/podcast-digest-agent
   uvicorn src.main:app --reload
   ```

2. **Test the API endpoint**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/tasks/process_youtube_url" \
   -H "Content-Type: application/json" \
   -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
   ```

3. **Verify task status and audio generation**
   ```bash
   # Replace {TASK_ID} with the actual task ID from step 2
   curl "http://localhost:8000/api/v1/status/{TASK_ID}"
   ```

4. **Check audio file serving**
   ```bash
   # Replace {AUDIO_FILENAME} with the actual filename from step 3
   curl "http://localhost:8000/api/v1/audio/{AUDIO_FILENAME}"
   ```

5. **Verify WebSocket connections**
   - Open browser developer tools
   - Navigate to the frontend
   - Submit a YouTube URL
   - Check Network tab for WebSocket connections and messages

## Acceptance Criteria

### Must Have Requirements ✅

- [ ] Pipeline runner reduced to <150 lines total
- [ ] All 4 identified simulation files deleted
- [ ] API functionality unchanged - all endpoints work identically
- [ ] Audio generation working - MP3 files created successfully
- [ ] WebSocket status updates working - real-time progress shown
- [ ] Error handling preserved - graceful failure handling
- [ ] Logging maintained - same level of debug information

### Should Have Requirements ✅

- [ ] Code coverage maintained - existing tests still pass
- [ ] Performance same or better - no regression in speed
- [ ] Memory usage improved - reduced complexity means less memory
- [ ] Logs are cleaner and more focused - less verbose output

### Could Have Requirements ✅

- [ ] Add simple integration test for the new pipeline
- [ ] Update inline documentation and comments
- [ ] Add performance benchmarks for comparison

## Risk Assessment

**Risk Level**: Low

This is primarily a code cleanup task that removes unused code and simplifies working functionality.

### Potential Issues

1. **Import errors** - Missing imports after file removal
2. **Missing dependencies** - Removed code that was actually needed
3. **API changes** - Unintentional changes to API behavior

### Mitigation Strategies

- Test thoroughly before committing changes
- Keep backup of original files until testing complete
- Use git branches for safe development
- Run comprehensive tests after each phase

## Success Metrics

### Code Quality Metrics

- **Lines of Code**: Reduce by ~400 lines
- **Cyclomatic Complexity**: Reduce pipeline complexity score
- **Test Coverage**: Maintain >80% coverage
- **Performance**: No regression in processing time

### Functional Metrics

- **API Response Time**: No increase in response time
- **Audio Quality**: No degradation in output quality
- **Error Rate**: No increase in error rates
- **Memory Usage**: Reduce memory footprint by 10-15%

## Implementation Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| Phase 1 | 30 min | Delete simulation files |
| Phase 2 | 2-3 hrs | Create simplified pipeline |
| Phase 3 | 30 min | Update API integration |
| Phase 4 | 15 min | Clean up utilities |
| Phase 5 | 30 min | Testing and verification |
| **Total** | **4-5 hrs** | **Complete cleanup** |

## Files Modified Summary

### Deleted Files (4 files)
- `src/processing/pipeline_simulation_backup.py` - 601 lines
- `src/tools/summarization_tools.py` - ~50 lines
- `src/tools/synthesis_tools.py` - ~50 lines
- `src/utils/audio_placeholder.py` - ~30 lines

### Created Files (1 file)
- `src/runners/simple_pipeline.py` - ~100 lines

### Modified Files (1 file)
- `src/api/v1/endpoints/tasks.py` - Import and function call changes only

### Deprecated Files (1 file)
- `src/runners/pipeline_runner.py` - Remove after testing complete

## Net Result

- **-400 lines of code** (significant reduction)
- **Same functionality** (no feature loss)
- **Cleaner architecture** (easier to maintain)
- **Better performance** (less complexity overhead)

## Definition of Done

The cleanup is complete when:

✅ All simulation files are deleted  
✅ Pipeline runner is simplified to <150 lines  
✅ All existing tests pass  
✅ API endpoints work identically to before  
✅ Audio generation produces identical output  
✅ WebSocket updates work properly  
✅ Error handling works as expected  
✅ Code is reviewed and approved  
✅ Documentation is updated if needed  
✅ Changes are committed to version control

This cleanup will result in a more maintainable, efficient, and cleaner codebase while preserving all existing functionality.