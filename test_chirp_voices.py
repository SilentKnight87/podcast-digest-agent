#!/usr/bin/env python3
"""
Test script to verify Chirp HD voices work correctly.
"""

import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_chirp_voices():
    """Test Chirp HD voices for both speakers."""
    try:
        from src.adk_tools.audio_tools import generate_audio_from_dialogue

        # Test dialogue
        dialogue = [
            {
                "speaker": "A",
                "line": "Hello! I'm testing the new Chirp HD voice. This is speaker A with the Charon voice.",
            },
            {
                "speaker": "B",
                "line": "And I'm speaker B with the Kore voice. These Chirp HD voices sound much more natural!",
            },
            {"speaker": "A", "line": "Absolutely! The quality improvement is remarkable."},
            {
                "speaker": "B",
                "line": "I agree. Let's use these for the podcast digest from now on.",
            },
        ]

        # Convert to JSON string as expected by the function
        import json

        dialogue_script = json.dumps(dialogue)

        # Create output directory
        output_dir = "./test_chirp_output"
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Testing Chirp HD voices...")

        # Generate audio
        result = generate_audio_from_dialogue(dialogue_script, output_dir)

        if result and os.path.exists(result):
            file_size = os.path.getsize(result)
            logger.info(f"✅ Success! Audio file created: {result}")
            logger.info(f"   File size: {file_size:,} bytes")
            logger.info("   You can play this file to hear the Chirp HD voices")
        else:
            logger.error("❌ Failed to generate audio")

    except Exception as e:
        logger.error(f"❌ Error during testing: {e}", exc_info=True)


if __name__ == "__main__":
    # Run the test
    test_chirp_voices()
