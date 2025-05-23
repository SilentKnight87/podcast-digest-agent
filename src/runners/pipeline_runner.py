"""
Pipeline Runner for orchestrating the podcast digest generation process.
"""
import logging
import json
from typing import List, Dict
import asyncio
import os
import tempfile
import shutil
from google.cloud import texttospeech_v1

from src.agents.transcript_fetcher import TranscriptFetcher
from src.agents.summarizer import SummarizerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.agents.audio_generator import AudioGenerator
from src.tools.transcript_tools import fetch_transcripts
from src.tools.audio_tools import generate_audio_segment_tool, combine_audio_segments_tool
from src.agents.base_agent import BaseAgentEvent, BaseAgentEventType

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates the sequence of agent calls for podcast digest generation."""

    def __init__(self, transcript_fetcher, summarizer, synthesizer, audio_generator):
        """Initialize with required agents."""
        self.transcript_fetcher = transcript_fetcher
        self.summarizer = summarizer
        self.synthesizer = synthesizer
        self.audio_generator = audio_generator
        self._temp_dirs = []
        logger.info("PipelineRunner initialized with agents.")

    def cleanup(self):
        """Clean up temporary directories."""
        for temp_dir in self._temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to remove {temp_dir}: {e}")
        self._temp_dirs.clear()

    async def _run_agent(self, agent, input_data):
        """Run an agent and get the final result."""
        try:
            async for event in agent.run_async(input_data):
                if isinstance(event, BaseAgentEvent):
                    if event.type == BaseAgentEventType.RESULT:
                        return event.payload
                    elif event.type == BaseAgentEventType.ERROR:
                        logger.error(f"Agent error: {event.payload.get('error', 'Unknown')}")
                        return None
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return None

    async def run_pipeline_async(self, video_ids: List[str], output_dir: str = "./output_audio", task_id: str = None) -> Dict:
        """Run the full pipeline from video IDs to final audio."""
        logger.info(f"Starting pipeline for {len(video_ids)} videos")
        
        try:
            # 1. Fetch transcripts
            logger.info("Fetching transcripts...")
            if task_id:
                from src.core import task_manager
                # Mark youtube-node as completed since we have the URL
                task_manager.update_agent_status(task_id, "youtube-node", "completed", progress=100)
                task_manager.update_data_flow_status(task_id, "youtube-node", "transcript-fetcher", "completed")
                task_manager.update_agent_status(task_id, "transcript-fetcher", "active", progress=10)
            
            fetch_result = fetch_transcripts.run(video_ids=video_ids)
            
            transcripts = {}
            failed_fetches = []
            
            if isinstance(fetch_result, dict):
                for video_id, result in fetch_result.items():
                    if isinstance(result, dict) and result.get("success") and result.get("transcript"):
                        transcripts[video_id] = result["transcript"]
                    else:
                        failed_fetches.append(video_id)
            
            if not transcripts:
                return self._error_response("No transcripts fetched", video_ids)

            # 2. Summarize transcripts
            logger.info("Summarizing transcripts...")
            if task_id:
                task_manager.update_agent_status(task_id, "transcript-fetcher", "completed", progress=100)
                task_manager.update_data_flow_status(task_id, "transcript-fetcher", "summarizer-agent", "completed")
                task_manager.update_task_processing_status(task_id, "processing", progress=25, current_agent_id="summarizer-agent")
                task_manager.update_agent_status(task_id, "summarizer-agent", "active", progress=10)
            
            summary_tasks = [self._run_agent(self.summarizer, t) for t in transcripts.values()]
            summary_results = await asyncio.gather(*summary_tasks)
            
            summaries = [r['summary'] for r in summary_results if isinstance(r, dict) and 'summary' in r]
            
            if not summaries:
                return self._error_response("Summarization failed", failed_fetches)

            # 3. Synthesize dialogue
            logger.info("Synthesizing dialogue...")
            if task_id:
                task_manager.update_agent_status(task_id, "summarizer-agent", "completed", progress=100)
                task_manager.update_data_flow_status(task_id, "summarizer-agent", "synthesizer-agent", "completed")
                task_manager.update_task_processing_status(task_id, "processing", progress=50, current_agent_id="synthesizer-agent")
                task_manager.update_agent_status(task_id, "synthesizer-agent", "active", progress=10)
            
            synthesis_result = await self._run_agent(self.synthesizer, json.dumps(summaries))
            
            dialogue_script = synthesis_result.get('dialogue', []) if isinstance(synthesis_result, dict) else []
            
            if not dialogue_script:
                return self._error_response("Dialogue synthesis failed", failed_fetches, len(summaries))

            # 4. Generate audio
            logger.info("Generating audio segments...")
            if task_id:
                task_manager.update_agent_status(task_id, "synthesizer-agent", "completed", progress=100)
                task_manager.update_data_flow_status(task_id, "synthesizer-agent", "audio-generator", "completed")
                task_manager.update_task_processing_status(task_id, "processing", progress=75, current_agent_id="audio-generator")
                task_manager.update_agent_status(task_id, "audio-generator", "active", progress=10)
            
            temp_dir = tempfile.mkdtemp(prefix="podcast_segments_")
            self._temp_dirs.append(temp_dir)
            
            async with texttospeech_v1.TextToSpeechAsyncClient() as tts_client:
                audio_tasks = []
                
                for i, segment in enumerate(dialogue_script):
                    speaker = segment.get("speaker", "A")
                    line = segment.get("line", "")
                    if not line:
                        continue
                        
                    output_path = os.path.join(temp_dir, f"segment_{i:03d}_{speaker}.mp3")
                    
                    task = generate_audio_segment_tool.run(
                        text=line,
                        speaker=speaker,
                        output_filepath=output_path,
                        tts_client=tts_client
                    )
                    audio_tasks.append(task)
                
                segment_files = []
                results = await asyncio.gather(*audio_tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, str):
                        segment_files.append(result)
                
                if not segment_files:
                    return self._error_response("Audio generation failed", failed_fetches, len(summaries), dialogue_script)
                
                # 5. Combine audio
                logger.info("Combining audio segments...")
                if task_id:
                    task_manager.update_agent_status(task_id, "audio-generator", "active", progress=80)
                
                final_audio_path = await combine_audio_segments_tool.run(
                    segment_filepaths=segment_files,
                    output_dir=output_dir
                )
                
                if final_audio_path:
                    logger.info(f"Pipeline completed successfully: {final_audio_path}")
                    if task_id:
                        task_manager.update_agent_status(task_id, "audio-generator", "completed", progress=100)
                        task_manager.update_data_flow_status(task_id, "audio-generator", "ui-player", "completed")
                        task_manager.update_agent_status(task_id, "ui-player", "completed", progress=100)
                        task_manager.update_task_processing_status(task_id, "completed", progress=100)
                    
                    return {
                        "status": "success",
                        "success": True,
                        "dialogue_script": dialogue_script,
                        "failed_transcripts": failed_fetches,
                        "summary_count": len(summaries),
                        "final_audio_path": final_audio_path,
                        "error": None
                    }
                else:
                    return self._error_response("Audio combination failed", failed_fetches, len(summaries), dialogue_script)
                    
        except Exception as e:
            logger.exception("Pipeline error")
            return self._error_response(str(e), video_ids)
        finally:
            self.cleanup()
    
    def _error_response(self, error_msg, failed_transcripts, summary_count=0, dialogue_script=None):
        """Create standardized error response."""
        return {
            "status": "failure",
            "success": False,
            "error": error_msg,
            "dialogue_script": dialogue_script or [],
            "failed_transcripts": failed_transcripts,
            "summary_count": summary_count,
            "final_audio_path": None
        }