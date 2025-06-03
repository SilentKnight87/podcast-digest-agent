"""Debug endpoints for testing proxy and transcript fetching."""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.adk_tools.transcript_tools import fetch_youtube_transcript
from src.config.proxy_config import ProxyManager

logger = logging.getLogger(__name__)

router = APIRouter()


class TestTranscriptRequest(BaseModel):
    """Request model for testing transcript fetch."""
    video_id: str


@router.post("/test-transcript")
async def test_transcript(request: TestTranscriptRequest):
    """Test transcript fetching with detailed error info."""
    try:
        # Get proxy config
        proxy_config = ProxyManager.get_proxy_config()
        proxy_info = {
            "proxy_enabled": proxy_config is not None,
            "proxy_type": type(proxy_config).__name__ if proxy_config else None,
        }
        
        if proxy_config and hasattr(proxy_config, 'url'):
            proxy_info["proxy_url"] = proxy_config.url
            
        logger.info(f"Testing transcript fetch for {request.video_id} with proxy: {proxy_info}")
        
        # Try to fetch transcript
        result = fetch_youtube_transcript(request.video_id)
        
        return {
            "proxy_info": proxy_info,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Test transcript error: {str(e)}", exc_info=True)
        return {
            "proxy_info": proxy_info if 'proxy_info' in locals() else None,
            "error": str(e),
            "error_type": type(e).__name__
        }