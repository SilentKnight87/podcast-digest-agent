from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from src.config.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/audio/{filename}", response_class=FileResponse, tags=["Audio"], name="get_audio_file")
async def get_audio_file(filename: str):
    """
    Serves a generated audio file.
    Ensure the filename is sanitized to prevent directory traversal.
    """
    # Basic sanitization
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = Path(settings.OUTPUT_AUDIO_DIR) / filename
    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"Audio file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Audio file not found.")
    
    # Ensure the file is within the designated audio directory
    try:
        # Resolve both paths to their absolute form to prevent traversal attacks
        base_dir_resolved = Path(settings.OUTPUT_AUDIO_DIR).resolve(strict=True)
        file_path_resolved = file_path.resolve(strict=True)
        
        # Check if the resolved file_path is a child of base_dir_resolved
        # or if it is the same as the base_dir_resolved (if OUTPUT_AUDIO_DIR is a file, which is unlikely but good to check parent)
        if base_dir_resolved != file_path_resolved.parent and base_dir_resolved not in file_path_resolved.parents:
             logger.error(f"Forbidden access attempt for audio file: {file_path_resolved} (base: {base_dir_resolved})")
             raise HTTPException(status_code=403, detail="Access to this file is forbidden.")

    except FileNotFoundError: # If strict=True and path doesn't exist
        logger.warning(f"Audio file not found or invalid path during resolution: {file_path}")
        raise HTTPException(status_code=404, detail="Audio file not found or invalid path.")
    except Exception as e:
        logger.error(f"Error resolving audio file path for {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while accessing file.")

    return FileResponse(file_path, media_type="audio/mpeg", filename=filename) 