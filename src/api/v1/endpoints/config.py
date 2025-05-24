from fastapi import APIRouter

from src.config.settings import settings
from src.models.api_models import ApiConfigResponse, ConfigOption

router = APIRouter()


@router.get("/config", response_model=ApiConfigResponse)
async def get_api_config():
    return ApiConfigResponse(
        available_tts_voices=[ConfigOption(**voice) for voice in settings.AVAILABLE_TTS_VOICES],
        available_summary_lengths=[
            ConfigOption(**length) for length in settings.AVAILABLE_SUMMARY_LENGTHS
        ],
        available_audio_styles=[ConfigOption(**style) for style in settings.AVAILABLE_AUDIO_STYLES],
    )
