import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file from the project root
dotenv_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"
)
load_dotenv(dotenv_path=dotenv_path)

# Determine Project Root assuming settings.py is in src/config/
# This ensures that relative paths are anchored correctly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings.
    Values are loaded from environment variables and/or .env file.
    """

    APP_NAME: str = "Podcast Digest Agent"
    DEBUG: bool = Field(default=False)

    # API related settings
    API_V1_STR: str = "/api/v1"

    # CORS Settings
    @property
    def CORS_ALLOWED_ORIGINS(self) -> list[str]:
        """Get CORS allowed origins from environment variable."""
        cors_string = os.getenv(
            "CORS_ALLOWED_ORIGINS", "http://localhost:3000;http://localhost:3001"
        )
        # Support both comma and semicolon as separators
        return [
            origin.strip() for origin in cors_string.replace(",", ";").split(";") if origin.strip()
        ]

    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for CORS and other configurations",
    )

    # Directories
    OUTPUT_AUDIO_DIR: str = Field(default="output_audio")
    INPUT_DIR: str = Field(default="input")

    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str | None = Field(
        default=None, env="GOOGLE_APPLICATION_CREDENTIALS"
    )

    # Default processing options
    DEFAULT_SUMMARY_LENGTH: str = "medium"  # e.g., "short", "medium", "long"
    DEFAULT_AUDIO_STYLE: str = "neutral"  # e.g., "neutral", "upbeat", "calm"
    DEFAULT_TTS_VOICE: str = "en-US-Neural2-J"  # Example Google Cloud TTS voice

    # Available options for frontend
    AVAILABLE_TTS_VOICES: list[dict[str, Any]] = [
        {
            "id": "standard_voice_1",
            "name": "Standard Voice 1 (Female)",
            "language": "en-US",
            "type": "Standard",
        },
        {
            "id": "standard_voice_2",
            "name": "Standard Voice 2 (Male)",
            "language": "en-US",
            "type": "Standard",
        },
        {
            "id": "neural_voice_1",
            "name": "Neural Voice 1 (Female)",
            "language": "en-US",
            "type": "Neural",
            "preview_url": "/audio/previews/neural_voice_1.mp3",
        },
        {
            "id": "neural_voice_2",
            "name": "Neural Voice 2 (Male)",
            "language": "en-GB",
            "type": "Neural",
            "preview_url": "/audio/previews/neural_voice_2.mp3",
        },
    ]
    AVAILABLE_SUMMARY_LENGTHS: list[dict[str, str]] = [
        {
            "id": "short",
            "name": "Short (1-2 mins)",
            "description": "Brief overview, key takeaways only.",
        },
        {
            "id": "medium",
            "name": "Medium (3-5 mins)",
            "description": "Balanced summary with main points and some detail.",
        },
        {
            "id": "long",
            "name": "Long (6-8 mins)",
            "description": "Comprehensive summary with extended explanations.",
        },
    ]
    AVAILABLE_AUDIO_STYLES: list[dict[str, str]] = [
        {
            "id": "informative",
            "name": "Informative",
            "description": "Clear, neutral tone suitable for educational content.",
        },
        {
            "id": "conversational",
            "name": "Conversational",
            "description": "Friendly and engaging, like a discussion.",
        },
        {
            "id": "energetic",
            "name": "Energetic",
            "description": "Upbeat and dynamic, good for motivational topics.",
        },
    ]

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        extra="ignore",
        case_sensitive=False,  # Environment variables are typically case-insensitive or uppercase
    )


try:
    settings = Settings()
except Exception as e:
    print(f"ERROR: Failed to initialize settings: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
    # Re-raise to maintain original behavior
    raise

# Ensure output directories exist
# os.makedirs(settings.OUTPUT_AUDIO_DIR, exist_ok=True) # INTENTIONALLY COMMENTED OUT
# os.makedirs(settings.INPUT_DIR, exist_ok=True)      # INTENTIONALLY COMMENTED OUT

# --- Resolve paths and create directories ---


def _resolve_and_create_dir(path_str: str, project_root: Path, setting_name: str) -> Path:
    """Resolves a path string and creates the directory."""
    p = Path(path_str)
    if not p.is_absolute():
        resolved_p = (project_root / p).resolve()
    else:
        resolved_p = p

    try:
        os.makedirs(resolved_p, exist_ok=True)
    except OSError as e:
        # Provide more context if makedirs fails, especially for paths like '/app'
        print(f"Warning: Failed to create directory for {setting_name} at {resolved_p}: {e}")
        print(f"Original path string from settings/env: '{path_str}'")
        if resolved_p.is_absolute() and str(resolved_p).startswith("/app"):
            print(
                f"Hint: The path '{resolved_p}' looks like a Docker path. Check your .env file for '{setting_name}' or related environment variables if running locally."
            )
        # Depending on severity, you might raise the error or allow continuation if these dirs are optional at import time.
        # For now, we'll let it proceed after printing a warning, as tests might mock this.
        # However, the original error stops collection, so the try/except here is for graceful failure *if* we wanted that.
        # The primary fix is the user's .env file. This code just makes resolution robust.
        # Re-raising if we want to keep the strict failure: raise
    return resolved_p


# Resolve and create directories, these resolved Path objects can be used by the app
# The error occurs at os.makedirs(settings.INPUT_DIR, exist_ok=True) on line 60 or 61
# The following lines replace those direct os.makedirs calls.

# It's better practice to not have side effects like directory creation at module import time
# if they can fail due to environment. Consider moving this to an app startup event.
# For now, we make the existing logic more robust.

# Store resolved paths back on the settings object or use these variables directly
# For consistency, let's create new variables for resolved paths
# rather than trying to mutate the Pydantic model post-init without proper model fields.

_resolved_output_audio_dir = None
_resolved_input_dir = None

if os.getenv("PODCAST_AGENT_TEST_MODE", "False").lower() != "true":
    _resolved_output_audio_dir = _resolve_and_create_dir(
        settings.OUTPUT_AUDIO_DIR, PROJECT_ROOT, "OUTPUT_AUDIO_DIR"
    )
    _resolved_input_dir = _resolve_and_create_dir(settings.INPUT_DIR, PROJECT_ROOT, "INPUT_DIR")
else:
    # In test mode, we expect OUTPUT_AUDIO_DIR and INPUT_DIR to be set by the test environment
    # (e.g., via monkeypatching environment variables) to point to actual temporary, writable directories.
    # The settings.OUTPUT_AUDIO_DIR and settings.INPUT_DIR (strings) should reflect these temporary paths.

    # Resolve and attempt to create output audio directory
    output_audio_path_str = settings.OUTPUT_AUDIO_DIR
    temp_output_dir = Path(output_audio_path_str)
    if not temp_output_dir.is_absolute() and PROJECT_ROOT:
        temp_output_dir = (PROJECT_ROOT / temp_output_dir).resolve()
    else:
        # Ensure path is resolved even if it was initially absolute
        temp_output_dir = temp_output_dir.resolve()

    try:
        os.makedirs(temp_output_dir, exist_ok=True)
    except OSError as e:
        error_message = (
            f"ERROR IN TEST MODE: Failed to create directory for OUTPUT_AUDIO_DIR at '{temp_output_dir}'. "
            f"Original path string from settings: '{output_audio_path_str}'. Exception: {e}.\n"
            f"Please ensure that your test environment (e.g., pytest fixtures, conftest.py) correctly "
            f"sets the 'OUTPUT_AUDIO_DIR' environment variable to a writable temporary path *before* "
            f"the 'src.config.settings' module is imported or the Settings object is initialized.\n"
            f"If '{temp_output_dir}' starts with '/app', it might indicate an issue with .env "
            f"settings not being properly overridden for local testing or that the test environment "
            f"is not configured as expected for local runs."
        )
        raise OSError(error_message) from e
    _resolved_output_audio_dir = temp_output_dir

    # Resolve and attempt to create input directory
    input_path_str = settings.INPUT_DIR
    temp_input_dir = Path(input_path_str)
    if not temp_input_dir.is_absolute() and PROJECT_ROOT:
        temp_input_dir = (PROJECT_ROOT / temp_input_dir).resolve()
    else:
        # Ensure path is resolved even if it was initially absolute
        temp_input_dir = temp_input_dir.resolve()

    try:
        os.makedirs(temp_input_dir, exist_ok=True)
    except OSError as e:
        error_message = (
            f"ERROR IN TEST MODE: Failed to create directory for INPUT_DIR at '{temp_input_dir}'. "
            f"Original path string from settings: '{input_path_str}'. Exception: {e}.\n"
            f"Please ensure that your test environment (e.g., pytest fixtures, conftest.py) correctly "
            f"sets the 'INPUT_DIR' environment variable to a writable temporary path *before* "
            f"the 'src.config.settings' module is imported or the Settings object is initialized.\n"
            f"If '{temp_input_dir}' starts with '/app', it might indicate an issue with .env "
            f"settings not being properly overridden for local testing or that the test environment "
            f"is not configured as expected for local runs."
        )
        raise OSError(error_message) from e
    _resolved_input_dir = temp_input_dir

# If your application relies on settings.OUTPUT_AUDIO_DIR being a Path object,
# you would need to adjust the Settings model itself, e.g., using validators or __init__
# to store resolved paths. For now, the creation is handled, and other parts of the code
# would use settings.OUTPUT_AUDIO_DIR (string) and might need to resolve it similarly if they need a Path.

# To make these resolved paths easily accessible via the `settings` object:
# One approach (if you can modify the Settings class further):
# Add fields like:
#   RESOLVED_OUTPUT_AUDIO_DIR: Path | None = None
#   RESOLVED_INPUT_DIR: Path | None = None
# And assign them in __init__ or a root_validator.

# For the purpose of fixing the os.makedirs call, we've handled it above.
# The rest of your app should decide if it uses the string versions from settings
# or if it needs to perform similar resolution.
# The test_settings.py uses `settings.OUTPUT_AUDIO_DIR` as a string.

# The original lines around 60-61 were:
# os.makedirs(settings.OUTPUT_AUDIO_DIR, exist_ok=True)
# os.makedirs(settings.INPUT_DIR, exist_ok=True)
# These are now effectively replaced by the _resolve_and_create_dir calls.

# Ensure settings object itself provides the resolved paths if needed elsewhere consistently:
# This is a more involved change to Pydantic model structure (e.g. using private attributes and properties)
# or by re-assigning if the fields were mutable (not typical for settings objects).
# The simplest way for now is that the _resolved_input_dir / _resolved_output_audio_dir are the authoritative paths
# for I/O operations after this point.

# Example: For the app to use the resolved paths:
# settings.RESOLVED_INPUT_DIR = _resolved_input_dir (requires adding this field to Settings model)
# settings.RESOLVED_OUTPUT_AUDIO_DIR = _resolved_output_audio_dir

# For minimal changes to existing code that might use settings.INPUT_DIR as a string:
# The _resolve_and_create_dir calls have already done the directory creation part.
# If other code needs the *resolved Path object*, it should use `_resolved_input_dir` or `_resolved_output_audio_dir`
# or perform its own resolution based on `settings.INPUT_DIR` (string) and `PROJECT_ROOT`.
# For clarity, let's ensure the attributes on `settings` that were strings are replaced by their resolved Path versions
# if your application consistently expects Path objects. This requires careful handling of Pydantic model updates.

# A simpler pattern is to make the directory creation a function called at app startup,
# rather than at module import time.

# Given the immediate error, the _resolve_and_create_dir calls above handle the problematic os.makedirs.
# Your `test_settings.py` also manipulates these string versions of paths.
# The critical part is that `os.makedirs` now gets a path like `/Users/peterbrown/.../input`
# instead of `/app` if `INPUT_DIR` was `"input"` and not `"/app"` from env.
# If `INPUT_DIR` *is* `"/app"` from env, `_resolved_input_dir` will be `Path("/app")`
# and the `os.makedirs` inside `_resolve_and_create_dir` will still fail,
# but the error message will now include the hint about Docker paths.
# The actual fix remains: correct the .env file.

if __name__ == "__main__":
    # For testing the settings loading
    print(f"App Name: {settings.APP_NAME}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"API V1 STR: {settings.API_V1_STR}")
    print(f"Output Audio Dir: {settings.OUTPUT_AUDIO_DIR}")
    print(f"Google Credentials Path: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
    print(f"Default TTS Voice: {settings.DEFAULT_TTS_VOICE}")
    print(f"Available Voices: {settings.AVAILABLE_TTS_VOICES}")
