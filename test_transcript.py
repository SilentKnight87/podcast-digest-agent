import logging
from urllib.parse import parse_qs, urlparse

from src.agents.transcript_fetcher import TranscriptFetcher

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    parsed_url = urlparse(url)
    if parsed_url.netloc == "youtu.be":
        return parsed_url.path[1:]
    if parsed_url.netloc in ("www.youtube.com", "youtube.com"):
        if parsed_url.path == "/watch":
            return parse_qs(parsed_url.query)["v"][0]
    return url


def main():
    # Initialize the transcript fetcher agent
    agent = TranscriptFetcher()

    # YouTube URL
    url = "https://www.youtube.com/watch?v=QN14IFM9s04&t=624s"
    video_id = extract_video_id(url)

    # Fetch the transcript
    logger.info(f"Fetching transcript for video: {video_id}")
    response = agent.fetch_transcript(video_id)

    if response["status"] == "success":
        logger.info("Transcript successfully fetched!")
        print("\nTranscript:")
        print("-" * 80)
        print(response["result"]["transcript"])
        print(f"\nTotal segments: {response['result']['segments']}")
    else:
        logger.error(f"Failed to fetch transcript: {response['error']}")


if __name__ == "__main__":
    main()
