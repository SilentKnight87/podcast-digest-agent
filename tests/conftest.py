import asyncio
import importlib  # Added for reloading module
import os
import sys

import pytest

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope="function", autouse=True)
def override_settings_for_tests(monkeypatch, tmp_path_factory):
    """Override settings to use temporary directories for tests and signal test mode."""
    temp_input_dir = tmp_path_factory.mktemp("test_input_data")
    temp_output_audio_dir = tmp_path_factory.mktemp("test_output_audio")

    monkeypatch.setenv("INPUT_DIR", str(temp_input_dir))
    monkeypatch.setenv("OUTPUT_AUDIO_DIR", str(temp_output_audio_dir))
    monkeypatch.setenv("PODCAST_AGENT_TEST_MODE", "True")  # Signal test mode

    # Force reload of the settings module to ensure it uses the monkeypatched env vars
    if "src.config.settings" in sys.modules:
        importlib.reload(sys.modules["src.config.settings"])
    else:
        # If not already imported, importing it here will use the patched env vars
        pass


@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
