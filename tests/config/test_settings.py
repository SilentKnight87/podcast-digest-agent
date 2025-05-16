import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock

# Temporarily adjust sys.path if tests are not picking up src module directly
# This might be needed depending on how pytest is configured and the project structure
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# The settings module will be imported dynamically in tests to allow for modifications
# to environment variables before settings are loaded.

def clear_env_vars(vars_to_clear):
    """Helper to unset environment variables for testing."""
    for var in vars_to_clear:
        if var in os.environ:
            del os.environ[var]

@pytest.fixture(autouse=True)
def manage_env_and_settings_module():
    """Fixture to ensure a clean environment for each settings test."""
    # Store original env vars that might be modified by tests
    original_env = os.environ.copy()
    
    # List of env vars that settings.py might use or tests might set
    potentially_modified_vars = [
        "APP_NAME", "DEBUG", "API_V1_STR", "OUTPUT_AUDIO_DIR", 
        "INPUT_DIR", "GOOGLE_APPLICATION_CREDENTIALS", 
        "DEFAULT_SUMMARY_LENGTH", "DEFAULT_AUDIO_STYLE", "DEFAULT_TTS_VOICE"
    ]
    
    # Unload settings module if already loaded to allow re-import with new env state
    if 'src.config.settings' in sys.modules:
        del sys.modules['src.config.settings']
        
    yield
    
    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)
    
    # Clean up settings module again to not affect other test files
    if 'src.config.settings' in sys.modules:
        del sys.modules['src.config.settings']


# Dynamically load .env from project root for tests
# Assuming tests/config/test_settings.py, .env is two levels up
DOTENV_PATH = Path(__file__).resolve().parent.parent.parent / '.env'
if DOTENV_PATH.exists():
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    # Fallback for cases where .env might not exist (e.g. CI without .env)
    # Or if you want to create a temporary .test.env
    print(f"Info: .env file not found at {DOTENV_PATH}. Using defaults or pre-set env vars.")


def test_default_settings_load():
    """Test that settings load with default values when no env vars are set."""
    vars_to_clear = [
        "DEBUG", "OUTPUT_AUDIO_DIR", "INPUT_DIR", 
        "GOOGLE_APPLICATION_CREDENTIALS", "DEFAULT_TTS_VOICE"
    ]
    clear_env_vars(vars_to_clear)

    # Ensure settings module is re-imported for this test
    if 'src.config.settings' in sys.modules:
        del sys.modules['src.config.settings']
    from src.config.settings import Settings

    settings_instance = Settings()
    
    assert settings_instance.APP_NAME == "Podcast Digest Agent"
    assert settings_instance.DEBUG is False
    assert settings_instance.API_V1_STR == "/api/v1"
    assert settings_instance.OUTPUT_AUDIO_DIR == "output_audio" # Default
    assert settings_instance.INPUT_DIR == "input" # Default
    assert settings_instance.GOOGLE_APPLICATION_CREDENTIALS is None # Default
    assert settings_instance.DEFAULT_TTS_VOICE == "en-US-Neural2-J" # Default
    assert len(settings_instance.AVAILABLE_TTS_VOICES) > 0
    assert len(settings_instance.AVAILABLE_SUMMARY_LENGTHS) > 0
    assert len(settings_instance.AVAILABLE_AUDIO_STYLES) > 0

def test_settings_load_from_env_vars():
    """Test that settings are correctly overridden by environment variables."""
    test_debug = "True"
    test_output_dir = "test_outputs"
    test_input_dir = "test_inputs"
    test_gac = "/fake/path/to/creds.json"
    test_voice = "en-GB-Wavenet-A"

    os.environ["DEBUG"] = test_debug
    os.environ["OUTPUT_AUDIO_DIR"] = test_output_dir
    os.environ["INPUT_DIR"] = test_input_dir
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = test_gac
    os.environ["DEFAULT_TTS_VOICE"] = test_voice
    
    # Ensure settings module is re-imported
    if 'src.config.settings' in sys.modules:
        del sys.modules['src.config.settings']
    from src.config.settings import Settings
    
    settings_instance = Settings()
    
    assert settings_instance.DEBUG is True
    assert settings_instance.OUTPUT_AUDIO_DIR == test_output_dir
    assert settings_instance.INPUT_DIR == test_input_dir
    assert settings_instance.GOOGLE_APPLICATION_CREDENTIALS == test_gac
    assert settings_instance.DEFAULT_TTS_VOICE == test_voice

    clear_env_vars(["DEBUG", "OUTPUT_AUDIO_DIR", "INPUT_DIR", "GOOGLE_APPLICATION_CREDENTIALS", "DEFAULT_TTS_VOICE"])

@patch('os.makedirs')
def test_directory_creation(mock_makedirs):
    """Test that os.makedirs is called to create output and input directories."""
    # Clear env vars to ensure default paths are used by settings, then re-import
    clear_env_vars(["OUTPUT_AUDIO_DIR", "INPUT_DIR"])
    if 'src.config.settings' in sys.modules:
        del sys.modules['src.config.settings']
    
    # This import will trigger the os.makedirs calls at the bottom of settings.py
    from src.config.settings import settings 
    
    expected_calls = [
        ((settings.OUTPUT_AUDIO_DIR,), {"exist_ok": True}),
        ((settings.INPUT_DIR,), {"exist_ok": True})
    ]
    
    # Check if mock_makedirs was called with the expected arguments
    # This is a bit tricky because the calls happen at import time.
    # We check the calls made *during the import of the module*.
    
    # For more robustness, one could also check if the directories actually exist after import,
    # but that would require creating/deleting them in a temp location.
    # Here, we just verify the intent to create.
    
    # Assert that makedirs was called for the output audio directory
    mock_makedirs.assert_any_call(settings.OUTPUT_AUDIO_DIR, exist_ok=True)
    # Assert that makedirs was called for the input directory
    mock_makedirs.assert_any_call(settings.INPUT_DIR, exist_ok=True)
    
    assert mock_makedirs.call_count >= 2 # It might be called more if other parts of settings use it

def test_settings_load_from_dotenv_file(tmp_path):
    """Test that settings can be loaded from a .env file."""
    # Create a temporary .env file
    dotenv_content = """
DEBUG=True
OUTPUT_AUDIO_DIR=dotenv_output
GOOGLE_APPLICATION_CREDENTIALS=dotenv_creds.json
"""
    # Create a .env file in a temporary directory that settings.py will discover
    # For this test to work perfectly, settings.py needs to be able to find this .env
    # The current settings.py looks for .env in the project root.
    # We will patch load_dotenv to use our temporary .env file.

    env_file = tmp_path / ".env"
    env_file.write_text(dotenv_content)

    with patch('src.config.settings.load_dotenv') as mock_load_dotenv, \
         patch('src.config.settings.dotenv_path', str(env_file)):
        
        # Force re-import of settings
        if 'src.config.settings' in sys.modules:
            del sys.modules['src.config.settings']
        from src.config.settings import Settings
        
        settings_instance = Settings()

    mock_load_dotenv.assert_called_once_with(dotenv_path=str(env_file))
    
    assert settings_instance.DEBUG is True
    assert settings_instance.OUTPUT_AUDIO_DIR == "dotenv_output"
    assert settings_instance.GOOGLE_APPLICATION_CREDENTIALS == "dotenv_creds.json"

# Note: The `sys.path.insert` is generally not the best practice if a proper project structure
# (e.g., using `src` layout with `pyproject.toml` or `setup.py`) and pytest configuration
# (e.g., `pythonpath` in `pytest.ini` or `pyproject.toml`) are in place.
# If `pytest` is run from the project root, it should typically find the `src` directory.
# The `manage_env_and_settings_module` fixture attempts to handle module reloading for settings.
# This is often necessary because Pydantic's BaseSettings reads environment variables upon module import. 