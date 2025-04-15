import os
import tempfile
import shutil
import logging
from pathlib import Path
import pytest
from unittest import mock
import main

def test_ensure_output_dir_creates_directory(tmp_path):
    test_dir = tmp_path / "output_audio"
    assert not test_dir.exists()
    main.ensure_output_dir(str(test_dir))
    assert test_dir.exists()

def test_read_input_urls_reads_urls(tmp_path):
    input_file = tmp_path / "youtube_links.txt"
    input_file.write_text("https://youtu.be/abc123\nhttps://youtu.be/def456\n")
    video_ids = main.read_input_urls(str(input_file))
    assert video_ids == ["abc123", "def456"]

def test_read_input_urls_handles_missing_file(tmp_path, caplog):
    caplog.set_level(logging.WARNING)
    input_file = tmp_path / "notfound.txt"
    urls = main.read_input_urls(str(input_file))
    assert urls == []
    assert "not found" in caplog.text

def test_read_input_urls_handles_empty_lines(tmp_path):
    input_file = tmp_path / "youtube_links.txt"
    input_file.write_text("https://youtu.be/abc123\n\n   \nhttps://youtu.be/def456\n")
    video_ids = main.read_input_urls(str(input_file))
    assert video_ids == ["abc123", "def456"]

def test_check_gcloud_adc_env(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/tmp/fake_creds.json")
    with mock.patch("os.path.exists", return_value=True):
        main.check_gcloud_adc()
    assert "GOOGLE_APPLICATION_CREDENTIALS" in caplog.text

def test_check_gcloud_adc_gcloud_default(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with mock.patch("os.path.exists", side_effect=lambda p: p.endswith("application_default_credentials.json")):
        main.check_gcloud_adc()
    assert "gcloud application-default login" in caplog.text

def test_check_gcloud_adc_missing(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with mock.patch("os.path.exists", return_value=False):
        main.check_gcloud_adc()
    assert "credentials not found" in caplog.text

def test_initialize_adk_and_clients_logs_info(caplog):
    caplog.set_level(logging.INFO)
    main.initialize_adk_and_clients()
    assert "would be initialized" in caplog.text 