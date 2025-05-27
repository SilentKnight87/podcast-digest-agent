"""
ADK-compatible audio generation tools.
"""
import json
import logging
import tempfile
from pathlib import Path

import pydub
from google.cloud import texttospeech_v1

logger = logging.getLogger(__name__)

# Voice configurations using Chirp HD voices for better quality
# Note: Chirp HD voices don't support SSML and don't require gender specification
DEFAULT_VOICE_CONFIG = {
    "A": {
        "language_code": "en-US",
        "name": "en-US-Chirp3-HD-Charon",  # Male-sounding voice
    },
    "B": {
        "language_code": "en-US",
        "name": "en-US-Chirp3-HD-Kore",  # Female-sounding voice
    },
}


def generate_audio_from_dialogue(dialogue_script: str, output_dir: str) -> str:
    """Generate audio from dialogue script using Google Cloud TTS.

    Args:
        dialogue_script: JSON string containing dialogue with speaker/line format
        output_dir: Directory to save the final audio file

    Returns:
        Path to the generated audio file
    """
    try:
        # Parse dialogue script
        dialogue = json.loads(dialogue_script)
        if not isinstance(dialogue, list):
            raise ValueError("Dialogue script must be a JSON array")

        # Create temporary directory for segments
        temp_dir = tempfile.mkdtemp(prefix="adk_audio_segments_")
        segment_files = []

        # Initialize TTS client (synchronous)
        tts_client = texttospeech_v1.TextToSpeechClient()

        # Generate audio segments
        for i, segment in enumerate(dialogue):
            speaker = segment.get("speaker", "A")
            line = segment.get("line", "")

            if not line.strip():
                continue

            # Generate audio for this segment
            segment_file = _generate_segment(tts_client, line, speaker, temp_dir, i)
            if segment_file:
                segment_files.append(segment_file)

        # Combine segments
        if segment_files:
            final_audio_path = _combine_segments(segment_files, output_dir)

            # Cleanup temporary files
            import shutil

            shutil.rmtree(temp_dir)

            # Log the successful generation
            logger.info(f"Successfully generated audio file: {final_audio_path}")

            # For ADK compatibility, return just the path string
            return final_audio_path
        else:
            logger.error("No audio segments generated")
            raise ValueError("No audio segments generated from dialogue script")

    except Exception as e:
        logger.error(f"Error generating audio: {e}", exc_info=True)
        raise


def _generate_segment(tts_client, text: str, speaker: str, temp_dir: str, index: int) -> str:
    """Generate a single audio segment."""
    try:
        voice_config = DEFAULT_VOICE_CONFIG.get(speaker, DEFAULT_VOICE_CONFIG["A"])

        synthesis_input = texttospeech_v1.SynthesisInput(text=text)
        voice = texttospeech_v1.VoiceSelectionParams(
            language_code=voice_config["language_code"],
            name=voice_config["name"],
        )
        audio_config = texttospeech_v1.AudioConfig(audio_encoding=texttospeech_v1.AudioEncoding.MP3)

        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Save segment file
        segment_path = Path(temp_dir) / f"segment_{index:03d}_{speaker}.mp3"
        with open(segment_path, "wb") as f:
            f.write(response.audio_content)

        return str(segment_path)

    except Exception as e:
        logger.error(f"Error generating segment {index}: {e}")
        return None


def _combine_segments(segment_files: list[str], output_dir: str) -> str:
    """Combine audio segments into final file."""
    try:
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Load and combine segments
        combined = pydub.AudioSegment.empty()
        for segment_file in sorted(segment_files):
            segment = pydub.AudioSegment.from_mp3(segment_file)
            combined += segment

        # Generate output filename
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_path / f"podcast_digest_{timestamp}.mp3"

        # Export final audio
        combined.export(str(output_file), format="mp3")

        logger.info(f"Combined audio saved to: {output_file}")
        return str(output_file)

    except Exception as e:
        logger.error(f"Error combining segments: {e}")
        raise
