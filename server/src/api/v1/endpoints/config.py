from fastapi import APIRouter
from fastapi.responses import JSONResponse

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


@router.get("/health/proxy")
async def check_proxy_health():
    """Check proxy connection health."""
    from src.utils.proxy_health import ProxyHealthChecker

    health_status = ProxyHealthChecker.check_proxy_status()
    status_code = 200 if health_status["status"] in ["healthy", "disabled"] else 503

    return JSONResponse(content=health_status, status_code=status_code)
