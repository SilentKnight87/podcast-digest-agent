import os
import logging
from pathlib import Path
from utils.input_processor import get_valid_video_ids

# --- Configuration ---
INPUT_DIR = os.getenv('INPUT_DIR', '/app/input')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/app/output_audio')
INPUT_FILE = os.path.join(INPUT_DIR, 'youtube_links.txt')
LOG_FILE = os.getenv('LOG_FILE')  # Optional log file path

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE) if LOG_FILE else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Step 1: Read and validate youtube_links.txt ---
def read_input_urls(input_file):
    try:
        video_ids = get_valid_video_ids(input_file)
        logger.info(f"Found {len(video_ids)} valid YouTube video IDs")
        return video_ids
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Error processing input file: {e}")
        return []

# --- Step 2: Ensure output directory exists ---
def ensure_output_dir(output_dir):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ensured at '{output_dir}'.")

# --- Step 3: Check Google Cloud ADC authentication ---
def check_gcloud_adc():
    adc_env = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    gcloud_config = os.path.expanduser('~/.config/gcloud/application_default_credentials.json')
    if adc_env and os.path.exists(adc_env):
        logger.info("Google Cloud ADC detected via GOOGLE_APPLICATION_CREDENTIALS.")
    elif os.path.exists(gcloud_config):
        logger.info("Google Cloud ADC detected via gcloud application-default login.")
    else:
        logger.warning("Google Cloud ADC credentials not found. Run 'gcloud auth application-default login' or set GOOGLE_APPLICATION_CREDENTIALS.")

# --- Step 4: Stub for ADK and Google Cloud client initialization ---
def initialize_adk_and_clients():
    # TODO: Initialize ADK, TTS, and Vertex AI clients here
    logger.info("(Stub) ADK and Google Cloud clients would be initialized here.")

# --- Main ---
def main():
    logger.info("--- Podcast Digest Agent: Initialization Start ---")
    logger.info(f"Input directory: {INPUT_DIR}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    
    # Process input and get valid video IDs
    video_ids = read_input_urls(INPUT_FILE)
    if not video_ids:
        logger.warning("No valid YouTube video IDs found. Exiting.")
        return
        
    ensure_output_dir(OUTPUT_DIR)
    check_gcloud_adc()
    initialize_adk_and_clients()
    logger.info("--- Initialization Complete ---")
    # Next steps: transcript fetching, summarization, etc.

if __name__ == '__main__':
    main() 