"""
Utility to create valid test audio files.
"""
import wave
import struct
import numpy as np
import math
from pathlib import Path


def create_test_wav(output_path, duration_seconds=5.0):
    """
    Create a valid WAV file with a simple tone.
    Uses a 440 Hz tone (A4 note).
    
    Args:
        output_path: Path to save the WAV file
        duration_seconds: Duration of the audio file in seconds
    """
    sample_rate = 44100
    num_channels = 1
    sample_width = 2  # 16-bit
    num_frames = int(sample_rate * duration_seconds)
    
    # Create a simple sine wave tone (440 Hz - A4 note)
    frequency = 440.0
    amplitude = 0.3  # Keep it at moderate volume
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with wave.open(output_path, 'wb') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        
        # Generate a more complex waveform with multiple frequencies for a richer sound
        for i in range(num_frames):
            # Time in seconds
            t = float(i) / sample_rate
            
            # Main tone (440 Hz)
            value = amplitude * math.sin(2.0 * math.pi * frequency * t)
            
            # Add a second harmonic (880 Hz) at lower amplitude 
            value += (amplitude * 0.5) * math.sin(2.0 * math.pi * (frequency * 2) * t)
            
            # Add a third harmonic (1320 Hz) at even lower amplitude
            value += (amplitude * 0.25) * math.sin(2.0 * math.pi * (frequency * 3) * t)
            
            # Apply slight amplitude modulation for a more natural sound
            mod = 1.0 + 0.1 * math.sin(2.0 * math.pi * 0.5 * t)
            value *= mod
            
            # Apply an envelope to avoid clicks at start/end
            if t < 0.1:  # Fade in
                value *= t / 0.1
            elif t > (duration_seconds - 0.1):  # Fade out
                value *= (duration_seconds - t) / 0.1
                
            # Ensure value is within [-1, 1]
            value = max(min(value, 1.0), -1.0)
            
            # Convert to 16-bit integer
            sample = int(value * 32767.0)
            
            # Pack as 16-bit little-endian
            packed_sample = struct.pack('<h', sample)
            wav_file.writeframes(packed_sample)
    
    print(f"Created WAV file at {output_path} with duration {duration_seconds} seconds")


def verify_wav_file(file_path):
    """
    Verify that a WAV file is valid and can be opened.
    
    Args:
        file_path: Path to the WAV file to verify
        
    Returns:
        dict: Information about the WAV file
    """
    try:
        with wave.open(file_path, 'rb') as wav_file:
            num_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()
            num_frames = wav_file.getnframes()
            duration = num_frames / frame_rate
            
            return {
                "valid": True,
                "num_channels": num_channels,
                "sample_width": sample_width,
                "frame_rate": frame_rate,
                "num_frames": num_frames,
                "duration": duration,
                "file_size": Path(file_path).stat().st_size
            }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Create a test WAV file
    output_path = "output_audio/test_tone.wav"
    create_test_wav(output_path, duration_seconds=10.0)
    
    # Verify the created file
    info = verify_wav_file(output_path)
    print(f"File verification: {info}")