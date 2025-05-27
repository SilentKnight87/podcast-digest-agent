#!/usr/bin/env python
"""Test endpoint to debug the hanging issue."""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/")
async def root():
    return {"status": "ok", "api_key_loaded": bool(os.getenv("GOOGLE_API_KEY"))}


@app.post("/test-process")
async def test_process():
    """Test the processing without background tasks."""
    try:
        # Import here to avoid issues
        from src.adk_runners.pipeline_runner import AdkPipelineRunner
        from src.config.settings import settings

        # Create a simple test
        pipeline = AdkPipelineRunner()

        # Run with a timeout
        result = await asyncio.wait_for(
            pipeline.run_async(
                video_ids=["NnFVDWQQUCw"],
                output_dir=settings.OUTPUT_AUDIO_DIR,
                task_id="test-task-123",
            ),
            timeout=30.0,  # 30 second timeout
        )

        return JSONResponse(content={"status": "success", "result": result})

    except asyncio.TimeoutError:
        return JSONResponse(
            content={"status": "error", "error": "Pipeline timed out after 30 seconds"},
            status_code=500,
        )
    except Exception as e:
        import traceback

        return JSONResponse(
            content={"status": "error", "error": str(e), "traceback": traceback.format_exc()},
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn

    print("Starting test server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
