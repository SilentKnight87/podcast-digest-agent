# Chirp HD Voice Upgrade

## Summary
Successfully upgraded the Text-to-Speech system from Wavenet voices to Google's Chirp HD voices for significantly better audio quality.

## Changes Made

### 1. ADK Audio Tools (`src/adk_tools/audio_tools.py`)
- Updated voice configuration from Journey to Chirp HD:
  - Speaker A: `en-US-Chirp3-HD-Charon` (male-sounding voice)
  - Speaker B: `en-US-Chirp3-HD-Kore` (female-sounding voice)
- Removed `ssml_gender` parameter as Chirp HD voices don't support it

### 2. Original Audio Tools (`src/tools/audio_tools.py`)
- Updated voice configuration from Wavenet to Chirp HD:
  - Speaker A: `en-US-Chirp3-HD-Charon` (male-sounding voice)
  - Speaker B: `en-US-Chirp3-HD-Kore` (female-sounding voice)
- Voice configuration already didn't require ssml_gender in the synthesis function

## Key Benefits of Chirp HD Voices
1. **Superior Quality**: Chirp HD voices are powered by cutting-edge LLMs and deliver unparalleled realism
2. **Emotional Resonance**: More natural and expressive speech synthesis
3. **Better Conversational Flow**: Ideal for dialogue between multiple speakers
4. **Latest Technology**: Uses Google's most advanced TTS models

## Important Notes
- Chirp HD voices don't support SSML input
- They don't support speaking rate and pitch audio parameters
- A-Law audio encoding is not supported
- Available in global, eu, and us endpoints only

## Testing
Created `test_chirp_voices.py` to verify the voices work correctly:
- Test passed successfully
- Generated audio file: 82,508 bytes
- Both voices (Charon and Kore) working properly

## Production Impact
- No code changes required beyond voice name updates
- Immediate quality improvement for all generated podcasts
- Backward compatible with existing API usage
- No changes needed to frontend or API endpoints
