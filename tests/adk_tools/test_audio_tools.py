"""
Tests for ADK-compatible audio tools.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adk_tools.audio_tools import (
    _combine_segments,
    _generate_segment,
    generate_audio_from_dialogue,
)


class TestGenerateAudioFromDialogue:
    """Test generate_audio_from_dialogue function."""

    @pytest.mark.asyncio
    async def test_successful_audio_generation(self):
        """Test successful audio generation from dialogue."""
        dialogue = [
            {"speaker": "A", "line": "Hello, welcome to the podcast digest!"},
            {"speaker": "B", "line": "Today we'll discuss amazing topics."},
        ]
        dialogue_script = json.dumps(dialogue)

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "src.adk_tools.audio_tools.texttospeech_v1.TextToSpeechAsyncClient"
            ) as mock_client:
                # Mock TTS client
                mock_tts = AsyncMock()
                mock_response = MagicMock()
                mock_response.audio_content = b"fake audio content"
                mock_tts.synthesize_speech.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_tts

                # Mock pydub
                with patch("src.adk_tools.audio_tools.pydub.AudioSegment") as mock_audio:
                    mock_segment = MagicMock()
                    mock_audio.from_mp3.return_value = mock_segment
                    mock_audio.empty.return_value = mock_segment
                    mock_segment.__iadd__.return_value = mock_segment

                    result = await generate_audio_from_dialogue(dialogue_script, temp_dir)

                    assert result["success"] is True
                    assert result["audio_path"] is not None
                    assert result["segment_count"] == 2
                    assert result["error"] is None

                    # Verify TTS was called for each line
                    assert mock_tts.synthesize_speech.call_count == 2

    @pytest.mark.asyncio
    async def test_invalid_json_dialogue(self):
        """Test handling of invalid JSON dialogue."""
        dialogue_script = "invalid json"

        with tempfile.TemporaryDirectory() as temp_dir:
            result = await generate_audio_from_dialogue(dialogue_script, temp_dir)

            assert result["success"] is False
            assert result["audio_path"] is None
            assert result["segment_count"] == 0
            assert "Expecting value" in result["error"]  # JSON decode error message

    @pytest.mark.asyncio
    async def test_non_list_dialogue(self):
        """Test handling of non-list dialogue format."""
        dialogue_script = json.dumps({"speaker": "A", "line": "Hello"})  # Not a list

        with tempfile.TemporaryDirectory() as temp_dir:
            result = await generate_audio_from_dialogue(dialogue_script, temp_dir)

            assert result["success"] is False
            assert result["audio_path"] is None
            assert "must be a JSON array" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_dialogue(self):
        """Test handling of empty dialogue."""
        dialogue_script = json.dumps([])

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.adk_tools.audio_tools.texttospeech_v1.TextToSpeechAsyncClient"):
                result = await generate_audio_from_dialogue(dialogue_script, temp_dir)

                assert result["success"] is False
                assert result["audio_path"] is None
                assert result["segment_count"] == 0
                assert "No audio segments generated" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_lines_skipped(self):
        """Test that empty lines are skipped."""
        dialogue = [
            {"speaker": "A", "line": "Hello"},
            {"speaker": "B", "line": ""},  # Empty line
            {"speaker": "A", "line": "   "},  # Whitespace only
            {"speaker": "B", "line": "Goodbye"},
        ]
        dialogue_script = json.dumps(dialogue)

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "src.adk_tools.audio_tools.texttospeech_v1.TextToSpeechAsyncClient"
            ) as mock_client:
                mock_tts = AsyncMock()
                mock_response = MagicMock()
                mock_response.audio_content = b"fake audio"
                mock_tts.synthesize_speech.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_tts

                with patch("src.adk_tools.audio_tools.pydub.AudioSegment") as mock_audio:
                    mock_segment = MagicMock()
                    mock_audio.from_mp3.return_value = mock_segment
                    mock_audio.empty.return_value = mock_segment
                    mock_segment.__iadd__.return_value = mock_segment

                    result = await generate_audio_from_dialogue(dialogue_script, temp_dir)

                    # Should only process 2 non-empty lines
                    assert result["segment_count"] == 2
                    assert mock_tts.synthesize_speech.call_count == 2

    @pytest.mark.asyncio
    async def test_tts_client_error(self):
        """Test handling of TTS client errors."""
        dialogue = [{"speaker": "A", "line": "Hello"}]
        dialogue_script = json.dumps(dialogue)

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "src.adk_tools.audio_tools.texttospeech_v1.TextToSpeechAsyncClient"
            ) as mock_client:
                mock_client.side_effect = Exception("TTS connection failed")

                result = await generate_audio_from_dialogue(dialogue_script, temp_dir)

                assert result["success"] is False
                assert "TTS connection failed" in result["error"]


class TestGenerateSegment:
    """Test _generate_segment helper function."""

    @pytest.mark.asyncio
    async def test_generate_segment_speaker_a(self):
        """Test generating segment for speaker A."""
        mock_tts = AsyncMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"audio for speaker A"
        mock_tts.synthesize_speech.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            result = await _generate_segment(mock_tts, "Hello from A", "A", temp_dir, 0)

            assert result is not None
            assert Path(result).exists()
            assert "segment_000_A.mp3" in result

            # Verify correct voice was used
            call_args = mock_tts.synthesize_speech.call_args[1]
            assert call_args["voice"].name == "en-US-Journey-D"

    @pytest.mark.asyncio
    async def test_generate_segment_speaker_b(self):
        """Test generating segment for speaker B."""
        mock_tts = AsyncMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"audio for speaker B"
        mock_tts.synthesize_speech.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            result = await _generate_segment(mock_tts, "Hello from B", "B", temp_dir, 1)

            assert result is not None
            assert Path(result).exists()
            assert "segment_001_B.mp3" in result

            # Verify correct voice was used
            call_args = mock_tts.synthesize_speech.call_args[1]
            assert call_args["voice"].name == "en-US-Journey-F"

    @pytest.mark.asyncio
    async def test_generate_segment_error(self):
        """Test handling of segment generation error."""
        mock_tts = AsyncMock()
        mock_tts.synthesize_speech.side_effect = Exception("TTS error")

        with tempfile.TemporaryDirectory() as temp_dir:
            result = await _generate_segment(mock_tts, "Test", "A", temp_dir, 0)

            assert result is None


class TestCombineSegments:
    """Test _combine_segments helper function."""

    @pytest.mark.asyncio
    async def test_combine_segments_success(self):
        """Test successful segment combination."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create fake segment files
            segment_files = []
            for i in range(3):
                segment_path = Path(temp_dir) / f"segment_{i:03d}.mp3"
                segment_path.write_bytes(b"fake audio data")
                segment_files.append(str(segment_path))

            with patch("src.adk_tools.audio_tools.pydub.AudioSegment") as mock_audio:
                mock_segment = MagicMock()
                mock_audio.from_mp3.return_value = mock_segment
                mock_audio.empty.return_value = mock_segment
                mock_segment.__iadd__.return_value = mock_segment

                result = await _combine_segments(segment_files, temp_dir)

                assert result is not None
                assert "podcast_digest_" in result
                assert result.endswith(".mp3")

                # Verify segments were loaded in order
                assert mock_audio.from_mp3.call_count == 3
                assert mock_segment.export.called

    @pytest.mark.asyncio
    async def test_combine_segments_error(self):
        """Test handling of combination error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            segment_files = ["/nonexistent/file.mp3"]

            with pytest.raises(Exception):
                await _combine_segments(segment_files, temp_dir)
