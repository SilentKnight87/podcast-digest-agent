import pytest
from input_processor import is_valid_youtube_url, process_urls, get_valid_video_ids
import logging
import tempfile
import os

# Test URL validation
def test_is_valid_youtube_url():
    # Test various YouTube URL formats
    assert is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ") == (True, "dQw4w9WgXcQ")
    assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == (True, "dQw4w9WgXcQ")
    assert is_valid_youtube_url("https://youtube.com/shorts/dQw4w9WgXcQ") == (True, "dQw4w9WgXcQ")
    
    # Test invalid URLs
    assert is_valid_youtube_url("https://example.com")[0] == False
    assert is_valid_youtube_url("not a url")[0] == False
    assert is_valid_youtube_url("")[0] == False

# Test URL processing
def test_process_urls(caplog):
    caplog.set_level(logging.INFO)
    
    urls = [
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/watch?v=abc123",
        "invalid url",
        "",  # empty line
        "   ",  # whitespace
    ]
    
    video_ids = process_urls(urls)
    
    assert len(video_ids) == 2
    assert "dQw4w9WgXcQ" in video_ids
    assert "abc123" in video_ids
    
    # Check logging
    assert "Valid YouTube URL found" in caplog.text
    assert "Invalid URL skipped" in caplog.text
    assert "Skipping empty line" in caplog.text

# Test file handling
def test_get_valid_video_ids(tmp_path):
    # Create test input file
    input_file = tmp_path / "test_urls.txt"
    input_file.write_text("""
    https://youtu.be/dQw4w9WgXcQ
    
    https://youtube.com/watch?v=abc123
    invalid url
    """)
    
    video_ids = get_valid_video_ids(str(input_file))
    
    assert len(video_ids) == 2
    assert "dQw4w9WgXcQ" in video_ids
    assert "abc123" in video_ids

def test_get_valid_video_ids_empty_file(tmp_path):
    # Create empty file
    input_file = tmp_path / "empty.txt"
    input_file.write_text("")
    
    video_ids = get_valid_video_ids(str(input_file))
    assert len(video_ids) == 0

def test_get_valid_video_ids_missing_file():
    with pytest.raises(FileNotFoundError):
        get_valid_video_ids("nonexistent.txt")

def test_get_valid_video_ids_invalid_permissions(tmp_path):
    # Create file with no read permissions
    input_file = tmp_path / "no_perms.txt"
    input_file.write_text("https://youtu.be/dQw4w9WgXcQ")
    input_file.chmod(0o000)  # No permissions
    
    with pytest.raises(IOError):
        get_valid_video_ids(str(input_file)) 