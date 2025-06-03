#!/usr/bin/env python3
"""Test proxy rotation with multiple YouTube videos."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

from src.config.settings import settings
from src.adk_tools.transcript_tools import fetch_youtube_transcript

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test videos from different channels - popular videos with known transcripts
TEST_VIDEOS = [
    ("UF8uR6Z6KLc", "Steve Jobs Stanford Commencement Address"),
    ("D_Vg4uyYwEk", "Steve Jobs introduces iPhone in 2007"),
    ("YWM6nz7IzkU", "Google Keynote (Google I/O'23)"), 
    ("zFRq7wV-618", "Sam Altman Keynote"),
    ("J5VgAOaQhXI", "Mark Zuckerberg at Harvard"),
    ("8JfDAm9v_7Q", "How does an Enigma machine work?"),
]

def test_proxy_rotation():
    """Test fetching transcripts with proxy rotation."""
    print("\n=== Testing Proxy Rotation ===")
    print(f"Proxy enabled: {settings.PROXY_ENABLED}")
    print(f"Proxy type: {settings.PROXY_TYPE}")
    print(f"Webshare username: {settings.WEBSHARE_PROXY_USERNAME}")
    print()
    
    successful = 0
    failed = 0
    
    for video_id, title in TEST_VIDEOS:
        print(f"\n--- Testing: {title} ---")
        print(f"Video ID: {video_id}")
        
        result = fetch_youtube_transcript(video_id)
        
        if result["success"]:
            successful += 1
            transcript_preview = result["transcript"][:200] + "..." if len(result["transcript"]) > 200 else result["transcript"]
            print(f"✅ SUCCESS: Fetched {result['segment_count']} segments")
            print(f"Transcript preview: {transcript_preview}")
        else:
            failed += 1
            print(f"❌ FAILED: {result['error']}")
    
    print(f"\n=== Summary ===")
    print(f"Total videos tested: {len(TEST_VIDEOS)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/len(TEST_VIDEOS))*100:.1f}%")
    
    if successful > 0:
        print("\n✅ Proxy rotation appears to be working!")
    else:
        print("\n❌ Proxy rotation may not be working properly")

if __name__ == "__main__":
    # Ensure proxy is enabled
    os.environ["PROXY_ENABLED"] = "true"
    os.environ["PROXY_TYPE"] = "webshare"
    
    test_proxy_rotation()