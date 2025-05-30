#!/usr/bin/env python
"""Start the FastAPI server with proper environment loading."""
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Change to project directory
os.chdir(project_root)

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Suppress expected Google GenAI function call warnings
logging.getLogger("google_genai.types").setLevel(logging.ERROR)

# Verify critical environment variables
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("WARNING: GOOGLE_API_KEY not found in environment")
else:
    print(f"✓ GOOGLE_API_KEY loaded (starts with {api_key[:10]}...)")

# Verify output directory
output_dir = os.getenv("OUTPUT_AUDIO_DIR", "output_audio")
output_path = project_root / output_dir
print(f"✓ Output directory: {output_path}")
if not output_path.exists():
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"  Created output directory: {output_path}")

# Import and run the app
if __name__ == "__main__":
    import uvicorn

    print(f"Starting Podcast Digest Agent API from {os.getcwd()}...")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to avoid issues
        log_level="info",
    )
