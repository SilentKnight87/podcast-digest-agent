"""
Simplified Pipeline Runner for podcast digest generation.
"""

import asyncio
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

from google.cloud import texttospeech_v1

from src.agents.audio_generator import AudioGenerator
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.transcript_fetcher import TranscriptFetcher
from src.tools.audio_tools import combine_audio_segments_tool, generate_audio_segment_tool
from src.tools.transcript_tools import fetch_transcripts

logger = logging.getLogger(__name__)


class SimplePipeline:
    """Simplified pipeline orchestrator for podcast digest generation."""

    def __init__(self):
        """Initialize with agents."""
        self.transcript_fetcher = TranscriptFetcher()
        self.summarizer = SummarizerAgent()
        self.synthesizer = SynthesizerAgent()
        self.audio_generator = AudioGenerator()
        self.temp_dirs: list[str] = []
        logger.info("SimplePipeline initialized")

    async def run_async(self, video_ids: list[str], output_dir: str, task_id: str = None) -> dict[str, Any]:
        """Run the complete pipeline asynchronously."""
        logger.info(f"Starting pipeline for {len(video_ids)} videos")

        try:
            async with texttospeech_v1.TextToSpeechAsyncClient() as tts_client:
                # Step 1: Fetch transcripts
                if task_id:
                    self._update_progress(task_id, 20, "transcript-fetcher", "Fetching transcripts...")
                
                transcript_results = fetch_transcripts.run(video_ids=video_ids)
                transcripts = self._extract_successful_transcripts(transcript_results)

                if not transcripts:
                    return self._error_result("No transcripts fetched", video_ids)

                # Step 2: Summarize transcripts
                if task_id:
                    self._update_progress(task_id, 40, "summarizer", "Summarizing transcripts...")
                
                summaries = await self._summarize_transcripts(list(transcripts.values()))

                if not summaries:
                    return self._error_result("No summaries generated", video_ids)

                # Step 3: Synthesize dialogue
                if task_id:
                    self._update_progress(task_id, 60, "synthesizer", "Synthesizing dialogue...")
                
                dialogue = await self._synthesize_dialogue(summaries)

                if not dialogue:
                    return self._error_result("No dialogue generated", video_ids)

                # Step 4: Generate audio
                if task_id:
                    self._update_progress(task_id, 80, "audio-generator", "Generating audio...")
                
                audio_path = await self._generate_audio(dialogue, output_dir, tts_client)

                if not audio_path:
                    return self._error_result("Audio generation failed", video_ids)

                if task_id:
                    self._update_progress(task_id, 95, "audio-generator", "Finalizing audio...")

                return {
                    "status": "success",
                    "success": True,
                    "dialogue_script": dialogue,
                    "final_audio_path": audio_path,
                    "summary_count": len(summaries),
                    "failed_transcripts": [],
                    "error": None,
                }

        except Exception as e:
            logger.exception(f"Pipeline error: {e}")
            return self._error_result(f"Pipeline error: {e}", video_ids)
        finally:
            self._cleanup()

    def _extract_successful_transcripts(self, results: dict[str, Any]) -> dict[str, str]:
        """Extract successful transcripts from results."""
        transcripts = {}
        for video_id, result in results.items():
            if isinstance(result, dict) and result.get("success"):
                transcript = result.get("transcript", "")
                if transcript:
                    transcripts[video_id] = transcript
        return transcripts

    async def _summarize_transcripts(self, transcripts: list[str]) -> list[str]:
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

    async def _synthesize_dialogue(self, summaries: list[str]) -> list[dict[str, Any]]:
        """Synthesize dialogue from summaries."""
        try:
            summaries_json = json.dumps(summaries)
            async for event in self.synthesizer.run_async(summaries_json):
                if event.type.name == "RESULT" and "dialogue" in event.payload:
                    return event.payload["dialogue"]
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
        return []

    async def _generate_audio(
        self, dialogue: list[dict[str, Any]], output_dir: str, tts_client
    ) -> str:
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
                        tts_client=tts_client,
                    )
                    tasks.append(task)

            # Wait for all segments
            segment_files = await asyncio.gather(*tasks, return_exceptions=True)
            valid_segments = [f for f in segment_files if isinstance(f, str)]

            if not valid_segments:
                return None

            # Combine segments
            final_path = await combine_audio_segments_tool.run(
                segment_filepaths=valid_segments, output_dir=output_dir
            )

            return final_path

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None

    def _error_result(self, error_msg: str, video_ids: list[str]) -> dict[str, Any]:
        """Create standardized error result."""
        return {
            "status": "error",
            "success": False,
            "dialogue_script": [],
            "final_audio_path": None,
            "summary_count": 0,
            "failed_transcripts": video_ids,
            "error": error_msg,
        }

    def _update_progress(self, task_id: str, progress: int, agent_id: str, message: str) -> None:
        """Update task progress via task manager."""
        try:
            from src.core import task_manager
            task_manager.update_task_processing_status(
                task_id=task_id,
                status="processing", 
                progress=progress,
                current_agent_id=agent_id
            )
            task_manager.add_timeline_event(
                task_id=task_id,
                event_type="progress_update",
                message=message,
                agent_id=agent_id
            )
            logger.info(f"Updated progress for task {task_id}: {progress}% - {message}")
        except Exception as e:
            logger.warning(f"Failed to update progress for task {task_id}: {e}")

    def _cleanup(self) -> None:
        """Clean up temporary directories."""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Cleanup failed for {temp_dir}: {e}")
        self.temp_dirs.clear()

    def run_pipeline(
        self, video_ids: list[str], output_dir: str = "./output_audio", task_id: str = None
    ) -> dict[str, Any]:
        """Synchronous wrapper for async pipeline."""
        return asyncio.run(self.run_async(video_ids, output_dir, task_id))
