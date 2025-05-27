"""
Validate ADK migration maintains all functionality.
"""
import asyncio

from src.adk_runners.pipeline_runner import AdkPipelineRunner
from src.runners.simple_pipeline import SimplePipeline


async def validate_migration():
    """Compare old vs new pipeline results."""

    test_video_id = "dQw4w9WgXcQ"  # Rick Roll for testing

    print("🔄 Testing ADK pipeline...")
    adk_runner = AdkPipelineRunner()
    adk_result = await adk_runner.run_async([test_video_id], "./test_output")

    print("🔄 Testing original pipeline...")
    original_runner = SimplePipeline()
    original_result = await original_runner.run_async([test_video_id], "./test_output")

    # Compare results
    adk_success = adk_result.get("success", False)
    original_success = original_result.get("success", False)

    print(f"ADK Result: {adk_success}")
    print(f"Original Result: {original_success}")

    if adk_success == original_success:
        print("✅ Migration validation PASSED - functionality maintained")
    else:
        print("❌ Migration validation FAILED - functionality differs")

    return adk_success == original_success


if __name__ == "__main__":
    asyncio.run(validate_migration())
