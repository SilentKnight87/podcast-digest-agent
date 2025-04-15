import re
import logging
from urllib.parse import urlparse, parse_qs
from typing import List, Tuple

logger = logging.getLogger(__name__)

def is_valid_youtube_url(url: str) -> Tuple[bool, str]:
    """
    Validates if a URL is a valid YouTube URL and extracts the video ID.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, video_id or error_message)
        
    Examples:
        >>> is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        (True, 'dQw4w9WgXcQ')
        
        >>> is_valid_youtube_url("https://youtube.com/watch?v=dQw4w9WgXcQ")
        (True, 'dQw4w9WgXcQ')
        
        >>> is_valid_youtube_url("https://example.com")
        (False, 'Not a YouTube URL')
    """
    # YouTube URL patterns
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^?]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^?]+)'
    ]
    
    # Try to match any of the patterns
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return True, match.group(1)
    
    return False, "Not a YouTube URL"

def process_urls(urls: List[str]) -> List[str]:
    """
    Processes a list of URLs, validating them and logging any issues.
    
    Args:
        urls (List[str]): List of URLs to process
        
    Returns:
        List[str]: List of valid YouTube video IDs
        
    Examples:
        >>> process_urls(["https://youtu.be/dQw4w9WgXcQ", "invalid"])
        ['dQw4w9WgXcQ']
    """
    valid_video_ids = []
    
    for url in urls:
        # Skip empty lines
        if not url.strip():
            logger.info(f"Skipping empty line")
            continue
            
        # Validate URL
        is_valid, result = is_valid_youtube_url(url)
        
        if is_valid:
            valid_video_ids.append(result)
            logger.info(f"Valid YouTube URL found: {url} (Video ID: {result})")
        else:
            logger.warning(f"Invalid URL skipped: {url} - {result}")
    
    return valid_video_ids

def get_valid_video_ids(input_file: str) -> List[str]:
    """
    Reads URLs from input file and returns valid YouTube video IDs.
    
    Args:
        input_file (str): Path to input file containing YouTube URLs
        
    Returns:
        List[str]: List of valid YouTube video IDs
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        IOError: If there's an error reading the file
    """
    try:
        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        if not urls:
            logger.warning(f"No URLs found in {input_file}")
            return []
            
        logger.info(f"Processing {len(urls)} URLs from {input_file}")
        return process_urls(urls)
        
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        raise
    except IOError as e:
        logger.error(f"Error reading input file: {e}")
        raise 