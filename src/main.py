import os
import logging
import json
from pathlib import Path

# Import agents
from agents.transcript_fetcher import TranscriptFetcher
from agents.summarizer import SummarizerAgent
from agents.synthesizer import SynthesizerAgent
from agents.audio_generator import AudioGenerator

# Import runner
from runners.pipeline_runner import PipelineRunner

# Import utils (assuming input processing logic exists)
from utils.input_processor import get_valid_video_ids

# --- Configuration ---
# Use Path for better path handling
BASE_DIR = Path(__file__).resolve().parent.parent # Project root (assuming src is one level down)
INPUT_DIR = Path(os.getenv('INPUT_DIR', BASE_DIR / 'input'))
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', BASE_DIR / 'output_audio'))
INPUT_FILE = INPUT_DIR / 'youtube_links.txt'
LOG_FILE = os.getenv('LOG_FILE')  # Optional log file path

# --- Logging Setup ---
log_handler = logging.FileHandler(LOG_FILE) if LOG_FILE else logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s',
    handlers=[log_handler]
)
logger = logging.getLogger(__name__)

# --- Step 1: Read and validate youtube_links.txt ---
def read_input_urls(input_file):
    try:
        # Assuming get_valid_video_ids returns a list of video IDs
        video_ids = get_valid_video_ids(str(input_file))
        logger.info(f"Found {len(video_ids)} valid YouTube video IDs in {input_file}")
        return video_ids
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        return []
    except Exception as e:
        logger.error(f"Error processing input file {input_file}: {e}")
        return []

# --- Step 2: Ensure output directory exists ---
def ensure_output_dir(output_dir):
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ensured at '{output_dir}'.")
    except Exception as e:
        logger.error(f"Failed to create output directory {output_dir}: {e}")
        raise # Reraise after logging if directory creation is critical

# --- Step 3: Check Google Cloud ADC authentication ---
def check_gcloud_adc():
    # (Keep existing ADC check logic)
    adc_env = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    gcloud_config = os.path.expanduser('~/.config/gcloud/application_default_credentials.json')
    if adc_env and Path(adc_env).exists():
        logger.info("Google Cloud ADC detected via GOOGLE_APPLICATION_CREDENTIALS.")
        return True
    elif Path(gcloud_config).exists():
        logger.info("Google Cloud ADC detected via gcloud default file.")
        return True
    else:
        logger.warning("Google Cloud ADC credentials not found.")
        return False

# --- Step 4: Initialize Agents and Runner ---
def initialize_pipeline():
    logger.info("Initializing agents...")
    try:
        transcript_fetcher = TranscriptFetcher()
        summarizer = SummarizerAgent()
        synthesizer = SynthesizerAgent()
        audio_generator = AudioGenerator()
        logger.info("Agents initialized successfully.")

        logger.info("Initializing pipeline runner...")
        pipeline_runner = PipelineRunner(
            transcript_fetcher=transcript_fetcher,
            summarizer=summarizer,
            synthesizer=synthesizer,
            audio_generator=audio_generator
        )
        logger.info("Pipeline runner initialized successfully.")
        return pipeline_runner
    except Exception as e:
        logger.exception("Fatal error during pipeline initialization.")
        return None

# --- Main Execution Logic ---
def main():
    logger.info("--- Podcast Digest Agent: Start --- ")
    logger.info(f"Input file path: {INPUT_FILE}")
    logger.info(f"Output directory path: {OUTPUT_DIR}")

    # Initial checks
    if not check_gcloud_adc():
       logger.error("ADC check failed. Please ensure authentication is configured. Exiting.")
       return

    try:
        ensure_output_dir(OUTPUT_DIR)
    except Exception:
        logger.error("Failed to ensure output directory. Exiting.")
        return

    # Read input
    video_ids = read_input_urls(INPUT_FILE)
    if not video_ids:
        logger.warning("No valid YouTube video IDs found or error reading input. Exiting.")
        return

    # Initialize pipeline components
    pipeline_runner = initialize_pipeline()
    if not pipeline_runner:
        logger.error("Pipeline initialization failed. Exiting.")
        return

    logger.info("--- Starting Pipeline Execution --- ")
    try:
        # Run the pipeline, passing the output directory
        result = pipeline_runner.run_pipeline(video_ids, output_dir=OUTPUT_DIR)

        logger.info("--- Pipeline Execution Complete --- ")

        # Process and display results
        if result and result.get("status") in ["success", "partial_failure"]:
            logger.info(f"Pipeline completed with status: {result.get('status')}.")
            dialogue = result.get("dialogue_script", [])
            if dialogue:
                logger.info("Generated Dialogue Script:")
                # Pretty print the JSON dialogue
                print(json.dumps(dialogue, indent=2))
            else:
                logger.info("No dialogue script was generated.")
            
            audio_file = result.get("final_audio_path")
            if audio_file:
                logger.info(f"Final audio file generated at: {audio_file}")
            else:
                logger.warning("Final audio file was not generated.")

            failed = result.get("failed_transcripts", [])
            if failed:
                logger.warning(f"Failed to fetch transcripts for {len(failed)} videos: {failed}")
        else:
            logger.error(f"Pipeline execution failed or did not return success status. Result: {result}")

    except Exception as e:
        logger.exception("An unexpected error occurred during pipeline execution.")

    logger.info("--- Podcast Digest Agent: Finish --- ")

if __name__ == '__main__':
    main() 