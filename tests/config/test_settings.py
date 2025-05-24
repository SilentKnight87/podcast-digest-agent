import os
import sys
from pathlib import Path
from unittest import mock
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

# Temporarily adjust sys.path if tests are not picking up src module directly
# This might be needed depending on how pytest is configured and the project structure
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
        "APP_NAME",
        "DEBUG",
        "API_V1_STR",
        "OUTPUT_AUDIO_DIR",
        "INPUT_DIR",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "DEFAULT_SUMMARY_LENGTH",
        "DEFAULT_AUDIO_STYLE",
        "DEFAULT_TTS_VOICE",
    ]

    # Unload settings module if already loaded to allow re-import with new env state
    if "src.config.settings" in sys.modules:
        del sys.modules["src.config.settings"]

    yield

    # Restore original environment variables
    os.environ.clear()
    os.environ.update(original_env)

    # Clean up settings module again to not affect other test files
    if "src.config.settings" in sys.modules:
        del sys.modules["src.config.settings"]


# Dynamically load .env from project root for tests
# Assuming tests/config/test_settings.py, .env is two levels up
DOTENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if DOTENV_PATH.exists():
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    # Fallback for cases where .env might not exist (e.g. CI without .env)
    # Or if you want to create a temporary .test.env
    print(f"Info: .env file not found at {DOTENV_PATH}. Using defaults or pre-set env vars.")


def test_default_settings_load():
    """Test that settings load with default values when no env vars are set."""
    vars_to_clear = [
        "DEBUG",
        "OUTPUT_AUDIO_DIR",
        "INPUT_DIR",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "DEFAULT_TTS_VOICE",
    ]
    clear_env_vars(vars_to_clear)

    # Ensure settings module is re-imported for this test
    if "src.config.settings" in sys.modules:
        del sys.modules["src.config.settings"]
    from src.config.settings import Settings

    settings_instance = Settings()

    assert settings_instance.APP_NAME == "Podcast Digest Agent"
    assert settings_instance.DEBUG is False
    assert settings_instance.API_V1_STR == "/api/v1"
    assert settings_instance.OUTPUT_AUDIO_DIR == "output_audio"  # Default
    assert settings_instance.INPUT_DIR == "input"  # Default
    assert settings_instance.GOOGLE_APPLICATION_CREDENTIALS is None  # Default
    assert settings_instance.DEFAULT_TTS_VOICE == "en-US-Neural2-J"  # Default
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
    if "src.config.settings" in sys.modules:
        del sys.modules["src.config.settings"]
    from src.config.settings import Settings

    settings_instance = Settings()

    assert settings_instance.DEBUG is True
    assert settings_instance.OUTPUT_AUDIO_DIR == test_output_dir
    assert settings_instance.INPUT_DIR == test_input_dir
    assert settings_instance.GOOGLE_APPLICATION_CREDENTIALS == test_gac
    assert settings_instance.DEFAULT_TTS_VOICE == test_voice

    clear_env_vars(
        [
            "DEBUG",
            "OUTPUT_AUDIO_DIR",
            "INPUT_DIR",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "DEFAULT_TTS_VOICE",
        ]
    )


@patch("os.makedirs")
def test_directory_creation(mock_makedirs):
    """Test that os.makedirs is called to create output and input directories."""
    # Clear env vars to ensure default paths are used by settings, then re-import
    clear_env_vars(["OUTPUT_AUDIO_DIR", "INPUT_DIR"])
    if "src.config.settings" in sys.modules:
        del sys.modules["src.config.settings"]

    # This import will trigger the os.makedirs calls at the bottom of settings.py
    from src.config.settings import settings

    expected_calls = [
        ((settings.OUTPUT_AUDIO_DIR,), {"exist_ok": True}),
        ((settings.INPUT_DIR,), {"exist_ok": True}),
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

    assert (
        mock_makedirs.call_count >= 2
    )  # It might be called more if other parts of settings use it


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

    with patch("src.config.settings.load_dotenv") as mock_load_dotenv, patch(
        "src.config.settings.dotenv_path", str(env_file)
    ):
        # Force re-import of settings
        if "src.config.settings" in sys.modules:
            del sys.modules["src.config.settings"]
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

# Store original environ
ORIG_ENV = os.environ.copy()


@pytest.fixture(autouse=True)
def reset_env_and_settings_modules():
    # Reset environment variables before each test
    os.environ.clear()
    os.environ.update(ORIG_ENV)

    # Remove settings from sys.modules to ensure it's reloaded
    # This is important because settings.py has side effects (like reading .env and creating dirs)
    import sys

    if "src.config.settings" in sys.modules:
        del sys.modules["src.config.settings"]
    if "src.config" in sys.modules:  # If src.config was imported
        del sys.modules["src.config"]


def test_default_settings_loaded(monkeypatch):
    # Ensure no .env file is loaded for this test, or mock its loading
    monkeypatch.setattr("dotenv.load_dotenv", lambda dotenv_path: None)

    # Mock os.makedirs to prevent actual directory creation during this test
    with mock.patch("os.makedirs") as mock_makedirs:
        from src.config.settings import PROJECT_ROOT, Settings

        # Temporarily remove specific env vars that might interfere if set globally
        monkeypatch.delenv("DEBUG", raising=False)
        monkeypatch.delenv("OUTPUT_AUDIO_DIR", raising=False)
        monkeypatch.delenv("INPUT_DIR", raising=False)
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

        settings_instance = Settings()

        assert settings_instance.APP_NAME == "Podcast Digest Agent"
        assert settings_instance.DEBUG is False
        assert settings_instance.API_V1_STR == "/api/v1"
        assert settings_instance.OUTPUT_AUDIO_DIR == "output_audio"  # Default string value
        assert settings_instance.INPUT_DIR == "input"  # Default string value
        assert settings_instance.GOOGLE_APPLICATION_CREDENTIALS is None
        assert settings_instance.DEFAULT_SUMMARY_LENGTH == "medium"
        assert settings_instance.DEFAULT_AUDIO_STYLE == "neutral"
        assert settings_instance.DEFAULT_TTS_VOICE == "en-US-Neural2-J"

        # Check that makedirs was called for default relative paths resolved against PROJECT_ROOT
        expected_output_path = (PROJECT_ROOT / "output_audio").resolve()
        expected_input_path = (PROJECT_ROOT / "input").resolve()

        calls = [
            mock.call(expected_output_path, exist_ok=True),
            mock.call(expected_input_path, exist_ok=True),
        ]
        # The order of calls to _resolve_and_create_dir in settings.py is OUTPUT_AUDIO_DIR then INPUT_DIR
        mock_makedirs.assert_has_calls(calls, any_order=False)


def test_settings_override_with_env_variables(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda dotenv_path: None)  # Disable .env loading

    test_google_creds_path = "/test/path/credentials.json"

    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("OUTPUT_AUDIO_DIR", "my_custom_output")
    monkeypatch.setenv("INPUT_DIR", "/abs/path/to/input")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", test_google_creds_path)
    monkeypatch.setenv("DEFAULT_TTS_VOICE", "custom-voice")

    with mock.patch("os.makedirs") as mock_makedirs:
        from src.config.settings import PROJECT_ROOT, Settings

        settings_instance = Settings()

        assert settings_instance.DEBUG is True
        assert settings_instance.OUTPUT_AUDIO_DIR == "my_custom_output"
        assert settings_instance.INPUT_DIR == "/abs/path/to/input"
        assert settings_instance.GOOGLE_APPLICATION_CREDENTIALS == test_google_creds_path
        assert settings_instance.DEFAULT_TTS_VOICE == "custom-voice"

        # Check that makedirs was called with the overridden paths
        expected_custom_output_path = (PROJECT_ROOT / "my_custom_output").resolve()
        expected_abs_input_path = Path("/abs/path/to/input").resolve()

        calls = [
            mock.call(expected_custom_output_path, exist_ok=True),
            mock.call(expected_abs_input_path, exist_ok=True),
        ]
        mock_makedirs.assert_has_calls(calls, any_order=False)


def test_dotenv_loading(tmp_path, monkeypatch):
    # Create a dummy .env file in a temporary directory
    env_content = """
    DEBUG=True
    OUTPUT_AUDIO_DIR=env_output_dir
    GOOGLE_APPLICATION_CREDENTIALS=/env/creds.json
    DEFAULT_SUMMARY_LENGTH=long
    # Test case insensitivity
    default_audio_style=test_style
    """
    # Create a dummy .env at the expected PROJECT_ROOT location for this test
    # settings.py looks for .env at PROJECT_ROOT / ".env"
    # We need to make PROJECT_ROOT point to tmp_path for this test

    test_project_root = tmp_path
    env_file = test_project_root / ".env"
    env_file.write_text(env_content)

    # Monkeypatch PROJECT_ROOT in the settings module
    # And also the dotenv_path variable used by load_dotenv directly
    monkeypatch.setattr("src.config.settings.PROJECT_ROOT", test_project_root)
    monkeypatch.setattr("src.config.settings.dotenv_path", str(env_file))

    with mock.patch("os.makedirs") as mock_makedirs:
        # Reload settings to apply the new PROJECT_ROOT and .env path
        import sys

        if "src.config.settings" in sys.modules:
            del sys.modules["src.config.settings"]

        from src.config.settings import Settings

        settings_instance = Settings()

    assert settings_instance.DEBUG is True
    assert settings_instance.OUTPUT_AUDIO_DIR == "env_output_dir"
    assert settings_instance.GOOGLE_APPLICATION_CREDENTIALS == "/env/creds.json"
    assert settings_instance.DEFAULT_SUMMARY_LENGTH == "long"
    assert (
        settings_instance.DEFAULT_AUDIO_STYLE == "test_style"
    )  # check case insensitivity from .env

    expected_output_path = (test_project_root / "env_output_dir").resolve()
    # INPUT_DIR was not in .env, so it should take its default "input"
    expected_input_path = (test_project_root / "input").resolve()

    calls = [
        mock.call(expected_output_path, exist_ok=True),
        mock.call(expected_input_path, exist_ok=True),
    ]
    mock_makedirs.assert_has_calls(calls, any_order=False)


def test_directory_creation_absolute_paths_from_env(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda dotenv_path: None)  # Disable .env loading

    abs_output_dir = "/tmp/abs_output_test"
    abs_input_dir = "/tmp/abs_input_test"

    monkeypatch.setenv("OUTPUT_AUDIO_DIR", abs_output_dir)
    monkeypatch.setenv("INPUT_DIR", abs_input_dir)

    with mock.patch("os.makedirs") as mock_makedirs:
        from src.config.settings import Settings

        settings_instance = Settings()  # Triggers _resolve_and_create_dir via module import

        assert settings_instance.OUTPUT_AUDIO_DIR == abs_output_dir
        assert settings_instance.INPUT_DIR == abs_input_dir

        calls = [
            mock.call(Path(abs_output_dir).resolve(), exist_ok=True),
            mock.call(Path(abs_input_dir).resolve(), exist_ok=True),
        ]
        mock_makedirs.assert_has_calls(calls, any_order=False)


def test_directory_creation_actually_creates_dirs(tmp_path, monkeypatch):
    # This test will *actually* create directories in tmp_path

    test_project_root = tmp_path
    # Define relative paths for the test
    relative_output_dir = "test_output"
    relative_input_dir = "test_input"

    # Monkeypatch PROJECT_ROOT in the settings module
    # And disable .env loading to ensure predictable paths
    import src.config.settings

    monkeypatch.setattr(src.config.settings, "PROJECT_ROOT", test_project_root)
    monkeypatch.setattr(
        src.config.settings, "dotenv_path", str(test_project_root / ".nonexistentenv")
    )
    monkeypatch.setattr(src.config.settings, "load_dotenv", lambda dotenv_path: None)

    # Set env vars for OUTPUT_AUDIO_DIR and INPUT_DIR to our relative paths
    monkeypatch.setenv("OUTPUT_AUDIO_DIR", relative_output_dir)
    monkeypatch.setenv("INPUT_DIR", relative_input_dir)

    # Reload settings module to apply monkeypatches and trigger dir creation
    import sys

    if "src.config.settings" in sys.modules:
        del sys.modules["src.config.settings"]

    # Import settings, this will run the module-level code including _resolve_and_create_dir
    from src.config.settings import settings  # Access the global instance

    # Verify the settings object has the overridden values
    assert settings.OUTPUT_AUDIO_DIR == relative_output_dir
    assert settings.INPUT_DIR == relative_input_dir

    # Check if directories were created
    expected_output_path = test_project_root / relative_output_dir
    expected_input_path = test_project_root / relative_input_dir

    assert expected_output_path.exists()
    assert expected_output_path.is_dir()
    assert expected_input_path.exists()
    assert expected_input_path.is_dir()

    # Clean up (optional, as tmp_path handles it, but good for clarity)
    # import shutil
    # shutil.rmtree(expected_output_path, ignore_errors=True)
    # shutil.rmtree(expected_input_path, ignore_errors=True)
