"""Proxy configuration management for YouTube transcript fetching."""

import logging

from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig

from src.config.settings import settings

logger = logging.getLogger(__name__)


class ProxyManager:
    """Manages proxy configuration for YouTube transcript fetching."""

    @staticmethod
    def get_proxy_config() -> WebshareProxyConfig | GenericProxyConfig | None:
        """Get appropriate proxy configuration based on settings."""
        if not settings.PROXY_ENABLED:
            logger.info("Proxy disabled, using direct connection")
            return None

        if settings.PROXY_TYPE == "webshare":
            if not settings.WEBSHARE_PROXY_USERNAME or not settings.WEBSHARE_PROXY_PASSWORD:
                raise ValueError("Webshare proxy credentials not configured")

            logger.info("Using Webshare residential proxy with automatic rotation")
            # Increase retries to give more chances for different IPs
            return WebshareProxyConfig(
                proxy_username=settings.WEBSHARE_PROXY_USERNAME,
                proxy_password=settings.WEBSHARE_PROXY_PASSWORD,
                retries_when_blocked=20,  # Increased from default 10
            )
        elif settings.PROXY_TYPE == "generic":
            # Support for custom proxy endpoints
            if not settings.GENERIC_PROXY_HTTP_URL:
                raise ValueError("Generic proxy URL not configured")

            logger.info("Using generic proxy configuration")
            return GenericProxyConfig(
                http_url=settings.GENERIC_PROXY_HTTP_URL,
                https_url=settings.GENERIC_PROXY_HTTPS_URL or settings.GENERIC_PROXY_HTTP_URL,
            )
        else:
            logger.warning(f"Unknown proxy type: {settings.PROXY_TYPE}")
            return None
