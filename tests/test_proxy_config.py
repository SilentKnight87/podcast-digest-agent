"""Tests for proxy configuration."""
import os
from unittest.mock import MagicMock, patch

import pytest
from youtube_transcript_api.proxies import GenericProxyConfig, WebshareProxyConfig

from src.config.proxy_config import ProxyManager


class TestProxyManager:
    """Test ProxyManager class."""

    def test_proxy_disabled(self):
        """Test proxy returns None when disabled."""
        with patch("src.config.proxy_config.settings") as mock_settings:
            mock_settings.PROXY_ENABLED = False
            assert ProxyManager.get_proxy_config() is None

    def test_webshare_proxy_config(self):
        """Test Webshare proxy configuration."""
        with patch("src.config.proxy_config.settings") as mock_settings:
            mock_settings.PROXY_ENABLED = True
            mock_settings.PROXY_TYPE = "webshare"
            mock_settings.WEBSHARE_PROXY_USERNAME = "test_user"
            mock_settings.WEBSHARE_PROXY_PASSWORD = "test_pass"

            config = ProxyManager.get_proxy_config()
            assert config is not None
            assert isinstance(config, WebshareProxyConfig)
            assert config.proxy_username == "test_user"
            assert config.proxy_password == "test_pass"

    def test_webshare_proxy_missing_credentials(self):
        """Test Webshare proxy with missing credentials."""
        with patch("src.config.proxy_config.settings") as mock_settings:
            mock_settings.PROXY_ENABLED = True
            mock_settings.PROXY_TYPE = "webshare"
            mock_settings.WEBSHARE_PROXY_USERNAME = None
            mock_settings.WEBSHARE_PROXY_PASSWORD = None

            with pytest.raises(ValueError, match="Webshare proxy credentials not configured"):
                ProxyManager.get_proxy_config()

    def test_generic_proxy_config(self):
        """Test generic proxy configuration."""
        with patch("src.config.proxy_config.settings") as mock_settings:
            mock_settings.PROXY_ENABLED = True
            mock_settings.PROXY_TYPE = "generic"
            mock_settings.GENERIC_PROXY_HTTP_URL = "http://proxy.example.com:8080"
            mock_settings.GENERIC_PROXY_HTTPS_URL = "https://proxy.example.com:8080"

            config = ProxyManager.get_proxy_config()
            assert config is not None
            assert isinstance(config, GenericProxyConfig)
            assert config.http_url == "http://proxy.example.com:8080"
            assert config.https_url == "https://proxy.example.com:8080"

    def test_generic_proxy_missing_url(self):
        """Test generic proxy with missing URL."""
        with patch("src.config.proxy_config.settings") as mock_settings:
            mock_settings.PROXY_ENABLED = True
            mock_settings.PROXY_TYPE = "generic"
            mock_settings.GENERIC_PROXY_HTTP_URL = None

            with pytest.raises(ValueError, match="Generic proxy URL not configured"):
                ProxyManager.get_proxy_config()

    def test_unknown_proxy_type(self):
        """Test unknown proxy type returns None."""
        with patch("src.config.proxy_config.settings") as mock_settings:
            mock_settings.PROXY_ENABLED = True
            mock_settings.PROXY_TYPE = "unknown"

            config = ProxyManager.get_proxy_config()
            assert config is None


class TestProxyHealthChecker:
    """Test ProxyHealthChecker class."""

    def test_proxy_disabled_health_check(self):
        """Test health check when proxy is disabled."""
        from src.utils.proxy_health import ProxyHealthChecker

        with patch("src.utils.proxy_health.ProxyManager.get_proxy_config", return_value=None):
            result = ProxyHealthChecker.check_proxy_status()
            assert result["status"] == "disabled"
            assert result["message"] == "Proxy not configured"

    def test_webshare_proxy_health_check_success(self):
        """Test successful Webshare proxy health check."""
        from src.utils.proxy_health import ProxyHealthChecker

        mock_proxy_config = MagicMock()
        mock_proxy_config.proxy_username = "test_user"
        mock_proxy_config.proxy_password = "test_pass"

        mock_response = MagicMock()
        mock_response.text = "192.168.1.1\n"
        mock_response.elapsed.total_seconds.return_value = 0.5

        with patch(
            "src.utils.proxy_health.ProxyManager.get_proxy_config", return_value=mock_proxy_config
        ):
            with patch("src.utils.proxy_health.requests.get", return_value=mock_response):
                result = ProxyHealthChecker.check_proxy_status()
                assert result["status"] == "healthy"
                assert result["ip"] == "192.168.1.1"
                assert result["response_time"] == 0.5

    def test_proxy_health_check_failure(self):
        """Test failed proxy health check."""
        from src.utils.proxy_health import ProxyHealthChecker

        mock_proxy_config = MagicMock()
        mock_proxy_config.proxy_username = "test_user"
        mock_proxy_config.proxy_password = "test_pass"

        with patch(
            "src.utils.proxy_health.ProxyManager.get_proxy_config", return_value=mock_proxy_config
        ):
            with patch(
                "src.utils.proxy_health.requests.get", side_effect=Exception("Connection failed")
            ):
                result = ProxyHealthChecker.check_proxy_status()
                assert result["status"] == "unhealthy"
                assert "Connection failed" in result["error"]


@pytest.mark.integration
@pytest.mark.skipif(
    not all([os.getenv("WEBSHARE_PROXY_USERNAME"), os.getenv("WEBSHARE_PROXY_PASSWORD")]),
    reason="Webshare credentials not provided",
)
def test_real_webshare_proxy_integration():
    """Test actual Webshare proxy integration."""
    import os

    from src.tools.transcript_tools import FetchTranscriptTool

    # This test requires real Webshare credentials
    username = os.getenv("WEBSHARE_PROXY_USERNAME")
    password = os.getenv("WEBSHARE_PROXY_PASSWORD")

    with patch.dict(
        os.environ,
        {
            "PROXY_ENABLED": "true",
            "PROXY_TYPE": "webshare",
            "WEBSHARE_PROXY_USERNAME": username,
            "WEBSHARE_PROXY_PASSWORD": password,
        },
    ):
        fetcher = FetchTranscriptTool()
        result = fetcher.run("dQw4w9WgXcQ")  # Known video ID
        assert result["success"] is True
        assert result["transcript"] is not None
        assert len(result["transcript"]) > 0
