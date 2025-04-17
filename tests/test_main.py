import os
import tempfile
import shutil
import logging
from pathlib import Path
import pytest
from unittest import mock
from unittest.mock import patch, MagicMock
from src.main import ensure_output_dir, read_input_urls, check_gcloud_adc, initialize_pipeline

def test_ensure_output_dir_creates_directory(tmp_path):
    test_dir = tmp_path / "output_audio"
    assert not test_dir.exists()
    ensure_output_dir(test_dir)
    assert test_dir.exists()

def test_read_input_urls_reads_urls(tmp_path):
    input_file = tmp_path / "youtube_links.txt"
    input_file.write_text("https://youtu.be/abc123\nhttps://youtu.be/def456\n")
    with mock.patch('src.main.get_valid_video_ids', return_value=["abc123", "def456"]):
        video_ids = read_input_urls(str(input_file))
    assert video_ids == ["abc123", "def456"]

def test_read_input_urls_handles_missing_file(tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    input_file = tmp_path / "notfound.txt"
    with mock.patch('src.main.get_valid_video_ids', side_effect=FileNotFoundError):
        urls = read_input_urls(str(input_file))
    assert urls == []
    assert "Input file not found" in caplog.text

def test_read_input_urls_handles_empty_lines(tmp_path):
    input_file = tmp_path / "youtube_links.txt"
    input_file.write_text("https://youtu.be/abc123\n\n   \nhttps://youtu.be/def456\n")
    with mock.patch('src.main.get_valid_video_ids', return_value=["abc123", "def456"]):
        video_ids = read_input_urls(str(input_file))
    assert video_ids == ["abc123", "def456"]

@patch('pathlib.Path.exists')
def test_check_gcloud_adc_env(mock_exists, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    fake_cred_path_str = "/tmp/fake_creds.json"
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", fake_cred_path_str)

    # Configure the mock exists method
    mock_exists.return_value = True # Assume env var path exists

    result = check_gcloud_adc()

    assert result is True
    # Verify Path.exists was called with the env var path
    mock_exists.assert_called_once_with() # Path object calls exists on itself
    # We can indirectly check the path by checking the log message which includes the path source
    assert "GOOGLE_APPLICATION_CREDENTIALS" in caplog.text # Check log

@patch('pathlib.Path.exists')
def test_check_gcloud_adc_gcloud_default(mock_exists, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    default_cred_path_str = os.path.expanduser('~/.config/gcloud/application_default_credentials.json')

    # Configure exists to return True as only the default path is checked here
    mock_exists.return_value = True

    result = check_gcloud_adc()

    assert result is True
    # Verify Path.exists was called once (only for the default path)
    mock_exists.assert_called_once()
    # Check log message indicates the default path was used
    assert "gcloud default file" in caplog.text # Check log

@patch('pathlib.Path.exists')
def test_check_gcloud_adc_missing(mock_exists, monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    # Mock Path.exists to always return False
    mock_exists.return_value = False

    result = check_gcloud_adc()

    assert result is False
    # Path.exists would be called for env var path (if set, here unset) and default path
    assert mock_exists.call_count >= 1 # Should be called at least for the default path
    assert "ADC credentials not found" in caplog.text

def test_initialize_pipeline_initializes_components(caplog):
    """Test that initialize_pipeline correctly initializes agents and the runner."""
    caplog.set_level(logging.INFO)

    # Mock the agent and runner constructors to prevent actual initialization
    with mock.patch('src.main.TranscriptFetcher') as mock_tf, \
         mock.patch('src.main.SummarizerAgent') as mock_sa, \
         mock.patch('src.main.SynthesizerAgent') as mock_syna, \
         mock.patch('src.main.AudioGenerator') as mock_ag, \
         mock.patch('src.main.PipelineRunner') as mock_pr:
        
        # Call the function
        pipeline_runner_instance = initialize_pipeline()

        # Assertions
        # Check that agent constructors were called
        mock_tf.assert_called_once()
        mock_sa.assert_called_once()
        mock_syna.assert_called_once()
        mock_ag.assert_called_once()
        
        # Check that PipelineRunner was called with mock agent instances
        mock_pr.assert_called_once_with(
            transcript_fetcher=mock_tf.return_value,
            summarizer=mock_sa.return_value,
            synthesizer=mock_syna.return_value,
            audio_generator=mock_ag.return_value
        )
        
        # Check that the returned value is the instance of PipelineRunner
        assert pipeline_runner_instance == mock_pr.return_value
        
        # Check logs
        assert "Initializing agents..." in caplog.text
        assert "Agents initialized successfully." in caplog.text
        assert "Initializing pipeline runner..." in caplog.text
        assert "Pipeline runner initialized successfully." in caplog.text 