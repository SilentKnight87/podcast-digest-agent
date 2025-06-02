"""In-memory audio storage for Cloud Run deployment."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# In-memory store for audio data with expiration
# Format: {filename: (audio_bytes, created_at)}
_audio_store: Dict[str, Tuple[bytes, datetime]] = {}

# Audio expires after 1 hour
AUDIO_EXPIRY_HOURS = 1


def store_audio(filename: str, audio_data: bytes) -> None:
    """Store audio data in memory."""
    _audio_store[filename] = (audio_data, datetime.now())
    logger.info(f"Stored audio file in memory: {filename} ({len(audio_data)} bytes)")
    
    # Clean up old files
    cleanup_expired_audio()


def get_audio(filename: str) -> Optional[bytes]:
    """Retrieve audio data from memory."""
    if filename in _audio_store:
        audio_data, created_at = _audio_store[filename]
        
        # Check if expired
        if datetime.now() - created_at > timedelta(hours=AUDIO_EXPIRY_HOURS):
            logger.info(f"Audio file expired: {filename}")
            del _audio_store[filename]
            return None
            
        logger.info(f"Retrieved audio file from memory: {filename}")
        return audio_data
    
    logger.warning(f"Audio file not found in memory: {filename}")
    return None


def cleanup_expired_audio() -> None:
    """Remove expired audio files from memory."""
    now = datetime.now()
    expired = []
    
    for filename, (_, created_at) in _audio_store.items():
        if now - created_at > timedelta(hours=AUDIO_EXPIRY_HOURS):
            expired.append(filename)
    
    for filename in expired:
        del _audio_store[filename]
        logger.info(f"Cleaned up expired audio: {filename}")