"""
Tests for the TranscriptFetcher agent.
"""
import pytest
from unittest.mock import Mock, patch
from src.agents.transcript_fetcher import TranscriptFetcher
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound
)

@pytest.fixture
def transcript_fetcher():
    return TranscriptFetcher()

def test_fetch_transcript_english_success(transcript_fetcher):
    mock_transcript = Mock()
    mock_transcript.fetch.return_value = [
        {'text': 'Hello'}, 
        {'text': 'world'}
    ]
    
    mock_transcript_list = Mock()
    mock_transcript_list.find_transcript.return_value = mock_transcript
    
    with patch.object(YouTubeTranscriptApi, 'list_transcripts', return_value=mock_transcript_list):
        result = transcript_fetcher.fetch_transcript('test_video_id')
        
    assert result == 'Hello world'
    mock_transcript_list.find_transcript.assert_called_once_with(['en'])

def test_fetch_transcript_english_fallback(transcript_fetcher):
    mock_transcript = Mock()
    mock_transcript.fetch.return_value = [
        {'text': 'Hello'}, 
        {'text': 'world'}
    ]
    
    mock_transcript_list = Mock()
    mock_transcript_list.find_transcript.side_effect = [
        NoTranscriptFound(),  # First call fails
        mock_transcript       # Second call succeeds
    ]
    
    with patch.object(YouTubeTranscriptApi, 'list_transcripts', return_value=mock_transcript_list):
        result = transcript_fetcher.fetch_transcript('test_video_id')
        
    assert result == 'Hello world'
    assert mock_transcript_list.find_transcript.call_count == 2
    mock_transcript_list.find_transcript.assert_called_with(['en-US', 'en-GB'])

def test_fetch_transcript_translation_fallback(transcript_fetcher):
    mock_transcript = Mock()
    mock_transcript.fetch.return_value = [
        {'text': 'Hello'}, 
        {'text': 'world'}
    ]
    mock_transcript.translate.return_value = mock_transcript
    
    mock_transcript_list = Mock()
    mock_transcript_list.find_transcript.side_effect = NoTranscriptFound()
    mock_transcript_list.find_manually_created_transcript.return_value = mock_transcript
    
    with patch.object(YouTubeTranscriptApi, 'list_transcripts', return_value=mock_transcript_list):
        result = transcript_fetcher.fetch_transcript('test_video_id')
        
    assert result == 'Hello world'
    mock_transcript.translate.assert_called_once_with('en')

def test_fetch_transcript_disabled(transcript_fetcher):
    with patch.object(YouTubeTranscriptApi, 'list_transcripts', side_effect=TranscriptsDisabled()):
        result = transcript_fetcher.fetch_transcript('test_video_id')
    assert result is None

def test_fetch_transcript_not_found(transcript_fetcher):
    mock_transcript_list = Mock()
    mock_transcript_list.find_transcript.side_effect = NoTranscriptFound()
    mock_transcript_list.find_manually_created_transcript.side_effect = NoTranscriptFound()
    
    with patch.object(YouTubeTranscriptApi, 'list_transcripts', return_value=mock_transcript_list):
        result = transcript_fetcher.fetch_transcript('test_video_id')
    assert result is None

def test_fetch_transcripts_multiple(transcript_fetcher):
    video_ids = ['video1', 'video2']
    
    # Mock successful transcript fetch for first video
    mock_transcript1 = Mock()
    mock_transcript1.fetch.return_value = [{'text': 'Hello world'}]
    mock_list1 = Mock()
    mock_list1.find_transcript.return_value = mock_transcript1
    
    # Mock failed transcript fetch for second video
    mock_list2 = Mock()
    mock_list2.find_transcript.side_effect = TranscriptsDisabled()
    
    with patch.object(YouTubeTranscriptApi, 'list_transcripts', side_effect=[mock_list1, mock_list2]):
        results = transcript_fetcher.fetch_transcripts(video_ids)
    
    assert results == {
        'video1': 'Hello world',
        'video2': None
    } 