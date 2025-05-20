"""
Utility to create a valid silent audio placeholder file.
"""
import shutil
from pathlib import Path
import requests

def create_silent_audio(file_path: str, duration_seconds: float = 1.0, format='mp3'):
    """
    Creates a placeholder audio file. For now, uses a sample file.
    
    Args:
        file_path: Path where the audio file should be created
        duration_seconds: Duration of the silent audio in seconds (not used for now)
        format: Audio format ('mp3' or 'wav')
    """
    path = Path(file_path)
    
    # For now, use a pre-recorded sample file
    # In the future, this would generate actual silent audio
    sample_file = Path(__file__).parent.parent.parent / "output_audio" / "sample.mp3"
    
    if sample_file.exists():
        # Copy the sample file
        shutil.copy(sample_file, file_path)
    else:
        # Create a minimal valid MP3 file with proper headers
        # This is a minimal MPEG-1 Layer III file with silence
        
        # ID3v2 header (10 bytes)
        id3_header = b'ID3\x03\x00\x00\x00\x00\x00\x00'
        
        # MPEG-1 Layer III header for 32 kbps, 44100 Hz, mono
        # Sync word (11 bits): 0x7FF
        # Version (2 bits): 11 = MPEG-1  
        # Layer (2 bits): 01 = Layer III
        # Protection (1 bit): 1 = No CRC
        # Bitrate (4 bits): 0001 = 32 kbps
        # Sample rate (2 bits): 00 = 44.1 kHz
        # Padding (1 bit): 1 = Padded
        # Private (1 bit): 0
        # Channel mode (2 bits): 11 = Mono
        # Mode extension (2 bits): 00
        # Copyright (1 bit): 0
        # Original (1 bit): 0
        # Emphasis (2 bits): 00 = None
        
        # This translates to: 0xFFFB1040
        frame_header = b'\xFF\xFB\x10\x40'
        
        # Frame size calculation for 32 kbps, 44.1 kHz mono
        # Frame size = 144 * bitrate / sample_rate + padding
        # = 144 * 32000 / 44100 + 1 = 105 bytes
        frame_size = 105
        frame_data = b'\x00' * (frame_size - 4)  # -4 for header
        
        # Number of frames needed for the duration
        # Each frame is 1152 samples / 44100 Hz = ~26.12 ms
        frames_needed = int(duration_seconds * 38.28)
        
        with open(file_path, 'wb') as f:
            # Write ID3 header
            f.write(id3_header)
            
            # Write MP3 frames
            for _ in range(frames_needed):
                f.write(frame_header)
                f.write(frame_data)
    
    return file_path