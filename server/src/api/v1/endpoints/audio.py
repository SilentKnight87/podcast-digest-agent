import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

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
    logger.info(f"Attempting to serve audio file: {file_path}")
    if not file_path.exists() or not file_path.is_file():
        logger.warning(f"Audio file not found: {file_path}")
        logger.warning(f"OUTPUT_AUDIO_DIR: {settings.OUTPUT_AUDIO_DIR}")
        logger.warning(f"Files in directory: {list(Path(settings.OUTPUT_AUDIO_DIR).glob('*'))}")
        raise HTTPException(status_code=404, detail="Audio file not found.")

    # Ensure the file is within the designated audio directory
    try:
        # Resolve both paths to their absolute form to prevent traversal attacks
        base_dir_resolved = Path(settings.OUTPUT_AUDIO_DIR).resolve(strict=True)
        file_path_resolved = file_path.resolve(strict=True)

        # Check if the resolved file_path is a child of base_dir_resolved
        # or if it is the same as the base_dir_resolved (if OUTPUT_AUDIO_DIR is a file, which is unlikely but good to check parent)
        if (
            base_dir_resolved != file_path_resolved.parent
            and base_dir_resolved not in file_path_resolved.parents
        ):
            logger.error(
                f"Forbidden access attempt for audio file: {file_path_resolved} (base: {base_dir_resolved})"
            )
            raise HTTPException(status_code=403, detail="Access to this file is forbidden.")

    except FileNotFoundError:  # If strict=True and path doesn't exist
        logger.warning(f"Audio file not found or invalid path during resolution: {file_path}")
        raise HTTPException(status_code=404, detail="Audio file not found or invalid path.")
    except Exception as e:
        logger.error(f"Error resolving audio file path for {filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while accessing file.")

    # Get file size for Content-Length header
    file_size = file_path.stat().st_size
    logger.info(f"Serving audio file: {filename}, size: {file_size} bytes")

    # Verify the file is actually an audio file by checking the first few bytes
    with open(file_path, "rb") as f:
        header = f.read(12)  # Read first 12 bytes

    # WAV file check (RIFF header)
    is_wav = header.startswith(b"RIFF") and b"WAVE" in header
    # MP3 file check (ID3 tag or MPEG frame header)
    is_mp3 = header.startswith(b"ID3") or (header[0:2] in [b"\xff\xfb", b"\xff\xfa", b"\xff\xf3"])

    logger.info(
        f"File format detection: is_wav={is_wav}, is_mp3={is_mp3}, header_hex={header.hex()}"
    )

    # Determine media type based on content detection and file extension
    if is_wav:
        media_type = "audio/wav"
    elif is_mp3:
        media_type = "audio/mpeg"
    elif filename.lower().endswith(".wav"):
        media_type = "audio/wav"
    elif filename.lower().endswith(".mp3"):
        media_type = "audio/mpeg"
    else:
        # Default to octet-stream if we can't determine the type
        logger.warning(
            f"Unable to determine audio type for {filename}, falling back to octet-stream"
        )
        media_type = "application/octet-stream"

    # Add CORS headers to ensure the file can be accessed from any origin
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Cache-Control": "public, max-age=3600",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Accept, Range",
        "Content-Disposition": f'inline; filename="{filename}"',
    }

    logger.info(f"Returning file {filename} with media type {media_type} and headers {headers}")

    # Return file with appropriate headers
    return FileResponse(file_path, media_type=media_type, filename=filename, headers=headers)
