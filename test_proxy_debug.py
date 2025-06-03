#!/usr/bin/env python3
"""Debug proxy issues with YouTube transcript API."""

import os
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Test video that should have transcripts
VIDEO_ID = "UF8uR6Z6KLc"  # Steve Jobs Stanford speech

print("Testing YouTube transcript API with Webshare proxy...")
print(f"Proxy username: {os.getenv('WEBSHARE_PROXY_USERNAME', 'Not set')}")
print()

try:
    # Create proxy config
    proxy_config = WebshareProxyConfig(
        proxy_username="grmrsnqt-1",
        proxy_password="5fhxe4162pg9",
        retries_when_blocked=20
    )
    
    print(f"Proxy URL: {proxy_config.url}")
    print(f"Retries when blocked: {proxy_config.retries_when_blocked}")
    print()
    
    # Try to fetch transcript
    print(f"Fetching transcript for video {VIDEO_ID}...")
    transcript_list = YouTubeTranscriptApi.get_transcript(
        VIDEO_ID, 
        proxies=proxy_config
    )
    
    print(f"✅ Success! Got {len(transcript_list)} segments")
    print(f"First segment: {transcript_list[0] if transcript_list else 'None'}")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()