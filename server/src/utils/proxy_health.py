"""Proxy health monitoring and status checking."""

import logging
from typing import Any

import requests

from src.config.proxy_config import ProxyManager

logger = logging.getLogger(__name__)


class ProxyHealthChecker:
    """Monitor proxy health and performance."""

    @staticmethod
    def check_proxy_status() -> dict[str, Any]:
        """Check if proxy is working correctly."""
        proxy_config = ProxyManager.get_proxy_config()

        if not proxy_config:
            return {"status": "disabled", "message": "Proxy not configured"}

        try:
            # For WebshareProxyConfig, we need to construct the proxy dict manually
            if hasattr(proxy_config, "proxy_username") and hasattr(proxy_config, "proxy_password"):
                # This is a WebshareProxyConfig
                proxy_url = f"http://{proxy_config.proxy_username}:{proxy_config.proxy_password}@p.webshare.io:80"
                proxy_dict = {"http": proxy_url, "https": proxy_url}
            elif hasattr(proxy_config, "http_url"):
                # This is a GenericProxyConfig
                proxy_dict = {
                    "http": proxy_config.http_url,
                    "https": proxy_config.https_url or proxy_config.http_url,
                }
            else:
                return {"status": "error", "error": "Unknown proxy configuration type"}

            # Test proxy with IP check service
            response = requests.get("https://ipv4.webshare.io/", proxies=proxy_dict, timeout=10)

            return {
                "status": "healthy",
                "ip": response.text.strip(),
                "response_time": response.elapsed.total_seconds(),
            }
        except Exception as e:
            logger.error(f"Proxy health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
