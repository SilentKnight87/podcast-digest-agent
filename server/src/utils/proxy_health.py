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
            # Check direct IP even when proxy is disabled
            direct_ip = None
            try:
                direct_response = requests.get("https://api.ipify.org?format=text", timeout=5)
                direct_ip = direct_response.text.strip()
            except Exception as e:
                logger.warning(f"Failed to get direct IP: {e}")
                
            return {
                "status": "disabled", 
                "message": "Proxy not configured",
                "direct_ip": direct_ip,
                "static_ip_configured": direct_ip == "34.132.37.143" if direct_ip else None
            }

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
            
            # Also check external IP without proxy to verify static IP configuration
            direct_ip = None
            try:
                direct_response = requests.get("https://api.ipify.org?format=text", timeout=5)
                direct_ip = direct_response.text.strip()
            except Exception as e:
                logger.warning(f"Failed to get direct IP: {e}")

            return {
                "status": "healthy",
                "proxy_ip": response.text.strip(),
                "direct_ip": direct_ip,
                "static_ip_configured": direct_ip == "34.132.37.143" if direct_ip else None,
                "response_time": response.elapsed.total_seconds(),
            }
        except Exception as e:
            logger.error(f"Proxy health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
