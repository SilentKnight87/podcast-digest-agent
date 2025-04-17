"""
Tools for generating audio using Google Cloud Text-to-Speech.
"""

import logging
import os
from typing import Dict, Optional, List
from datetime import datetime

from google.cloud import texttospeech
from google.api_core import exceptions as google_exceptions
from pydub import AudioSegment

from ..agents.base_agent import Tool

logger = logging.getLogger(__name__)

# --- Configuration ---

# Define voice configurations for speakers A and B
# Using Wavenet voices as specified in requirements
DEFAULT_VOICE_CONFIG: Dict[str, Dict[str, str]] = {
    "A": {
        "language_code": "en-US",
        "name": "en-US-Wavenet-D", # Example Wavenet Male
        "ssml_gender": texttospeech.SsmlVoiceGender.MALE
    },
    "B": {
        "language_code": "en-US",
        "name": "en-US-Wavenet-F", # Example Wavenet Female
        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE
    }
}

# Define audio encoding (MP3 recommended for output, LINEAR16 for intermediate if needed)
AUDIO_ENCODING = texttospeech.AudioEncoding.MP3

# --- Core TTS Function ---

def synthesize_speech_segment(
    text: str,
    speaker: str, # Should be 'A' or 'B'
    output_filepath: str,
    tts_client: Optional[texttospeech.TextToSpeechClient] = None,
    voice_config: Dict[str, Dict[str, str]] = DEFAULT_VOICE_CONFIG,
    audio_encoding: texttospeech.AudioEncoding = AUDIO_ENCODING
) -> Optional[str]:
    """Synthesizes speech for a text segment and saves it to a file.

    Args:
        text: The text to synthesize.
        speaker: The speaker identifier ('A' or 'B').
        output_filepath: The path to save the generated MP3 audio file.
        tts_client: An optional pre-initialized TextToSpeechClient.
        voice_config: Dictionary defining voice parameters for speakers 'A' and 'B'.
        audio_encoding: The desired audio encoding (e.g., MP3, LINEAR16).

    Returns:
        The output_filepath if synthesis was successful, None otherwise.
    """
    if not text:
        logger.warning("Skipping synthesis for empty text.")
        return None

    if speaker not in voice_config:
        logger.error(f"Invalid speaker ID: {speaker}. Must be one of {list(voice_config.keys())}")
        return None

    try:
        # Initialize client if not provided
        client = tts_client or texttospeech.TextToSpeechClient()

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=voice_config[speaker]["language_code"],
            name=voice_config[speaker]["name"]
            # ssml_gender can be specified if needed, but name usually suffices
        )

        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=audio_encoding
        )

        logger.info(f"Synthesizing speech for speaker {speaker} to {output_filepath}...")
        # Perform the text-to-speech request
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

        # The response's audio_content is binary.
        with open(output_filepath, "wb") as out_file:
            out_file.write(response.audio_content)
            logger.info(f"Audio content written to file: {output_filepath}")
        return output_filepath

    except google_exceptions.GoogleAPICallError as e:
        logger.error(f"Google Cloud TTS API error for speaker {speaker}: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during speech synthesis for speaker {speaker}: {e}")
        return None

# --- Audio Concatenation ---

def concatenate_audio_segments(
    segment_filepaths: List[str],
    output_dir: str,
    output_filename_base: str = "podcast_digest"
) -> Optional[str]:
    """Concatenates multiple audio segments into a single file.

    Args:
        segment_filepaths: A list of paths to the audio segment files (MP3 format).
        output_dir: The directory to save the final concatenated file.
        output_filename_base: The base name for the output file (timestamp added).

    Returns:
        The full path to the final concatenated audio file if successful, None otherwise.
    """
    if not segment_filepaths:
        logger.warning("No audio segments provided for concatenation.")
        return None

    logger.info(f"Concatenating {len(segment_filepaths)} audio segments...")
    combined_audio = None

    try:
        for i, segment_path in enumerate(segment_filepaths):
            if not os.path.exists(segment_path):
                logger.error(f"Segment file not found: {segment_path}. Skipping concatenation.")
                return None
            
            logger.debug(f"Loading segment {i+1}/{len(segment_filepaths)}: {segment_path}")
            segment_audio = AudioSegment.from_mp3(segment_path)

            if combined_audio is None:
                combined_audio = segment_audio
            else:
                combined_audio += segment_audio
        
        if combined_audio is None: # Should not happen if list is not empty and files exist
            logger.error("Failed to load any audio segments.")
            return None

        # --- Output Handling (Requirement 5.8) ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{output_filename_base}_{timestamp}.mp3"
        final_output_path = os.path.join(output_dir, output_filename)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"Exporting combined audio to: {final_output_path}")
        combined_audio.export(final_output_path, format="mp3")
        logger.info("Concatenation and export complete.")
        return final_output_path

    except FileNotFoundError as e:
        logger.error(f"Error during concatenation: {e}") # Should be caught above, but belt-and-suspenders
        return None
    except Exception as e:
        # Catch potential pydub errors (e.g., ffmpeg issues, corrupted files)
        logger.exception(f"Error during audio concatenation or export: {e}")
        return None

# --- Tool Classes ---

class GenerateAudioSegmentTool(Tool):
    """Tool for generating a single audio segment."""
    name: str = "generate_audio_segment"
    description: str = "Generates a single audio file (MP3) for a given text segment and speaker ('A' or 'B')"

    def run(self, text: str, speaker: str, output_filepath: str) -> Optional[str]:
        """Run the audio generation tool."""
        return synthesize_speech_segment(text, speaker, output_filepath)

class CombineAudioSegmentsTool(Tool):
    """Tool for combining multiple audio segments."""
    name: str = "combine_audio_segments"
    description: str = "Combines multiple audio segments into a single audio file"

    def run(self, segment_filepaths: List[str], output_dir: str, output_filename_base: str = "podcast_digest") -> Optional[str]:
        """Run the audio combination tool."""
        return concatenate_audio_segments(segment_filepaths, output_dir, output_filename_base)

# Create tool instances
generate_audio_segment_tool = GenerateAudioSegmentTool()
combine_audio_segments_tool = CombineAudioSegmentsTool()

# Example usage (for testing)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    script = [
        {"speaker": "A", "line": "Hello, this is Speaker A testing the synthesis."}, 
        {"speaker": "B", "line": "And this is Speaker B responding."},
        {"speaker": "A", "line": "It seems to be working."}, 
    ]
    # Use a temporary directory for segments
    temp_segment_dir = "./temp_audio_segments"
    # Define the final output directory from requirements
    final_output_dir = "./output_audio" 
    
    # Ensure clean start for temp dir if it exists
    if os.path.exists(temp_segment_dir):
        import shutil
        shutil.rmtree(temp_segment_dir)
    os.makedirs(temp_segment_dir)

    client = texttospeech.TextToSpeechClient() # Initialize once
    segment_files = []
    for i, segment in enumerate(script):
        # Save segments to the temporary directory
        output_file = os.path.join(temp_segment_dir, f"segment_{i}_{segment['speaker']}.mp3")
        result = synthesize_speech_segment(
            text=segment["line"],
            speaker=segment["speaker"],
            output_filepath=output_file,
            tts_client=client
        )
        if result:
            segment_files.append(result)
        else:
            logger.error(f"Failed to generate segment {i}")
    
    if segment_files:
        print(f"Generated segment files: {segment_files}")
        # Concatenate segments into the final output directory
        final_audio_file = concatenate_audio_segments(
            segment_filepaths=segment_files,
            output_dir=final_output_dir 
        )
        if final_audio_file:
            print(f"Successfully concatenated audio to: {final_audio_file}")
        else:
            print("Failed to concatenate audio segments.")
        
        # Optional: Clean up temporary segment files
        # print(f"Cleaning up temporary directory: {temp_segment_dir}")
        # import shutil
        # shutil.rmtree(temp_segment_dir)
    else:
        print("No segments were generated to concatenate.") 