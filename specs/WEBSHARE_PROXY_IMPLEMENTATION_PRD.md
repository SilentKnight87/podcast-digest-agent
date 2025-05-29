# Webshare Residential Proxy Implementation PRD

## Executive Summary

This document outlines the implementation of Webshare residential proxies to resolve YouTube transcript fetching issues in production. The Podcast Digest Agent deployed on Google Cloud Run is currently blocked by YouTube due to IP restrictions on cloud provider addresses. This PRD details the integration of Webshare's residential proxy service to bypass these restrictions while maintaining system reliability and performance.

## Problem Statement

- **Current Issue**: YouTube blocks transcript requests from Google Cloud Run IP addresses
- **Error**: `youtube_transcript_api._errors.TranscriptsDisabled: No transcripts were found for any of the requested language codes`
- **Root Cause**: YouTube detects and blocks requests from cloud provider IP ranges
- **Impact**: Complete failure of transcript fetching in production, rendering the application unusable

## Solution Overview

Implement Webshare residential proxy integration using the youtube-transcript-api's built-in proxy support. Webshare provides access to over 30 million residential IP addresses that appear as regular home internet connections to YouTube.

## Technical Requirements

### 1. Webshare Account Setup

- **Service**: Webshare Residential Proxy Plan
- **API Access**: Token-based authentication
- **Proxy Type**: Residential (not datacenter)
- **Geographic Distribution**: US-based IPs preferred for YouTube content
- **Bandwidth**: Estimate ~100MB per transcript fetch

### 2. Environment Configuration

Add new environment variables:
```bash
# Webshare Proxy Configuration
WEBSHARE_API_TOKEN=your-api-token
WEBSHARE_PROXY_USERNAME=your-proxy-username
WEBSHARE_PROXY_PASSWORD=your-proxy-password
PROXY_ENABLED=true
PROXY_TYPE=webshare  # Options: webshare, generic, none
```

### 3. Code Implementation

#### 3.1 Create Proxy Configuration Module

Create `src/config/proxy_config.py`:
```python
from typing import Optional, Union
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages proxy configuration for YouTube transcript fetching."""

    @staticmethod
    def get_proxy_config() -> Optional[Union[WebshareProxyConfig, GenericProxyConfig]]:
        """Get appropriate proxy configuration based on settings."""
        if not settings.PROXY_ENABLED:
            logger.info("Proxy disabled, using direct connection")
            return None

        if settings.PROXY_TYPE == "webshare":
            if not settings.WEBSHARE_PROXY_USERNAME or not settings.WEBSHARE_PROXY_PASSWORD:
                raise ValueError("Webshare proxy credentials not configured")

            logger.info("Using Webshare residential proxy")
            return WebshareProxyConfig(
                proxy_username=settings.WEBSHARE_PROXY_USERNAME,
                proxy_password=settings.WEBSHARE_PROXY_PASSWORD,
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
```

#### 3.2 Update Settings

Update `src/config/settings.py`:
```python
# Proxy Configuration
PROXY_ENABLED: bool = Field(default=False, env="PROXY_ENABLED")
PROXY_TYPE: str = Field(default="none", env="PROXY_TYPE")

# Webshare Proxy
WEBSHARE_API_TOKEN: Optional[str] = Field(default=None, env="WEBSHARE_API_TOKEN")
WEBSHARE_PROXY_USERNAME: Optional[str] = Field(default=None, env="WEBSHARE_PROXY_USERNAME")
WEBSHARE_PROXY_PASSWORD: Optional[str] = Field(default=None, env="WEBSHARE_PROXY_PASSWORD")

# Generic Proxy Support
GENERIC_PROXY_HTTP_URL: Optional[str] = Field(default=None, env="GENERIC_PROXY_HTTP_URL")
GENERIC_PROXY_HTTPS_URL: Optional[str] = Field(default=None, env="GENERIC_PROXY_HTTPS_URL")
```

#### 3.3 Update Transcript Tools

Modify both `src/tools/transcript_tools.py` and `src/adk_tools/transcript_tools.py`:

```python
from youtube_transcript_api import YouTubeTranscriptApi
from src.config.proxy_config import ProxyManager

class TranscriptFetcher:
    def __init__(self):
        """Initialize transcript fetcher with proxy configuration."""
        self.proxy_config = ProxyManager.get_proxy_config()

    def fetch_transcript(self, video_id: str, languages: list[str] = None) -> str:
        """Fetch transcript using proxy if configured."""
        try:
            if self.proxy_config:
                # Use proxy-enabled API instance
                api = YouTubeTranscriptApi(proxy_config=self.proxy_config)
                transcript_list = api.list_transcripts(video_id)
            else:
                # Use default API (direct connection)
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Rest of the implementation remains the same
            ...
        except Exception as e:
            logger.error(f"Failed to fetch transcript: {e}")
            raise
```

### 4. Deployment Configuration

#### 4.1 Update Cloud Run Deployment

Update `scripts/deploy-backend.sh`:
```bash
# Add proxy environment variables
PROXY_ENV_VARS=""
if [ ! -z "$WEBSHARE_PROXY_USERNAME" ]; then
    PROXY_ENV_VARS="${PROXY_ENV_VARS} --update-env-vars PROXY_ENABLED=true"
    PROXY_ENV_VARS="${PROXY_ENV_VARS} --update-env-vars PROXY_TYPE=webshare"
    PROXY_ENV_VARS="${PROXY_ENV_VARS} --update-env-vars WEBSHARE_PROXY_USERNAME=${WEBSHARE_PROXY_USERNAME}"
    PROXY_ENV_VARS="${PROXY_ENV_VARS} --update-env-vars WEBSHARE_PROXY_PASSWORD=${WEBSHARE_PROXY_PASSWORD}"
fi

# Deploy with proxy configuration
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_URL} \
    --region ${REGION} \
    --platform managed \
    --allow-unauthenticated \
    --min-instances 0 \
    --max-instances 100 \
    --port 8000 \
    --update-env-vars "GOOGLE_API_KEY=${GOOGLE_API_KEY}" \
    --update-env-vars "CORS_ALLOWED_ORIGINS=${CORS_ORIGINS}" \
    --update-env-vars "FRONTEND_URL=${FRONTEND_URL}" \
    ${PROXY_ENV_VARS}
```

#### 4.2 Update Docker Configuration

No changes needed to Dockerfile, but ensure proxy credentials are managed securely and not included in the image.

### 5. Monitoring and Error Handling

#### 5.1 Proxy Health Check

Create `src/utils/proxy_health.py`:
```python
import requests
from typing import Dict, Optional
from src.config.proxy_config import ProxyManager
import logging

logger = logging.getLogger(__name__)

class ProxyHealthChecker:
    """Monitor proxy health and performance."""

    @staticmethod
    def check_proxy_status() -> Dict[str, any]:
        """Check if proxy is working correctly."""
        proxy_config = ProxyManager.get_proxy_config()

        if not proxy_config:
            return {"status": "disabled", "message": "Proxy not configured"}

        try:
            # Test proxy with IP check service
            if hasattr(proxy_config, 'get_proxy_dict'):
                proxy_dict = proxy_config.get_proxy_dict()
            else:
                # Construct proxy dict for requests
                proxy_dict = {
                    'http': proxy_config.http_url,
                    'https': proxy_config.https_url or proxy_config.http_url
                }

            response = requests.get(
                'https://ipv4.webshare.io/',
                proxies=proxy_dict,
                timeout=10
            )

            return {
                "status": "healthy",
                "ip": response.text.strip(),
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            logger.error(f"Proxy health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
```

#### 5.2 Add Health Check Endpoint

Update `src/api/v1/endpoints/config.py`:
```python
@router.get("/health/proxy")
async def check_proxy_health():
    """Check proxy connection health."""
    from src.utils.proxy_health import ProxyHealthChecker

    health_status = ProxyHealthChecker.check_proxy_status()
    status_code = 200 if health_status["status"] in ["healthy", "disabled"] else 503

    return JSONResponse(content=health_status, status_code=status_code)
```

### 6. Fallback Strategy

Implement a fallback mechanism for when proxies fail:

```python
class TranscriptFetcherWithFallback:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.max_retries = 3

    async def fetch_with_fallback(self, video_id: str) -> Optional[str]:
        """Try fetching with proxy, fallback to direct if needed."""
        errors = []

        # Try with proxy first
        if self.proxy_manager.get_proxy_config():
            for attempt in range(self.max_retries):
                try:
                    return await self._fetch_with_proxy(video_id)
                except Exception as e:
                    errors.append(f"Proxy attempt {attempt + 1}: {e}")
                    logger.warning(f"Proxy fetch failed: {e}")

        # Try direct connection as last resort
        try:
            logger.info("Attempting direct connection (may fail on Cloud Run)")
            return await self._fetch_direct(video_id)
        except Exception as e:
            errors.append(f"Direct connection: {e}")

        # All attempts failed
        raise Exception(f"All transcript fetch attempts failed: {'; '.join(errors)}")
```

### 7. Cost Estimation

- **Webshare Residential Proxy**: ~$30-50/month for starter plan
- **Bandwidth**: ~100MB per transcript × estimated usage
- **API Calls**: Included in proxy plan
- **Additional Cloud Run costs**: Minimal (proxy adds ~100ms latency)

### 8. Security Considerations

1. **Credential Storage**: Use Google Secret Manager for proxy credentials
2. **IP Rotation**: Enable automatic IP rotation in Webshare dashboard
3. **Rate Limiting**: Implement rate limiting to avoid proxy abuse
4. **Monitoring**: Set up alerts for proxy failures and unusual usage

### 9. Testing Strategy

#### 9.1 Unit Tests

Create `tests/test_proxy_config.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from src.config.proxy_config import ProxyManager

def test_proxy_disabled():
    """Test proxy returns None when disabled."""
    with patch('src.config.settings.settings.PROXY_ENABLED', False):
        assert ProxyManager.get_proxy_config() is None

def test_webshare_proxy_config():
    """Test Webshare proxy configuration."""
    with patch.multiple('src.config.settings.settings',
                       PROXY_ENABLED=True,
                       PROXY_TYPE='webshare',
                       WEBSHARE_PROXY_USERNAME='test_user',
                       WEBSHARE_PROXY_PASSWORD='test_pass'):
        config = ProxyManager.get_proxy_config()
        assert config is not None
        assert hasattr(config, 'proxy_username')
```

#### 9.2 Integration Tests

```python
@pytest.mark.integration
async def test_transcript_fetch_with_proxy():
    """Test actual transcript fetching with proxy."""
    # This test should be skipped in CI/CD without proxy credentials
    if not os.getenv("WEBSHARE_PROXY_USERNAME"):
        pytest.skip("Proxy credentials not available")

    fetcher = TranscriptFetcher()
    transcript = await fetcher.fetch_transcript("dQw4w9WgXcQ")  # Known video ID
    assert transcript is not None
    assert len(transcript) > 0
```

### 10. Implementation Timeline

1. **Phase 1** (Day 1-2): Account setup and credential configuration
   - Create Webshare account
   - Set up residential proxy plan
   - Configure API credentials

2. **Phase 2** (Day 3-4): Code implementation
   - Implement ProxyManager
   - Update transcript tools
   - Add health check endpoints

3. **Phase 3** (Day 5): Testing
   - Unit tests
   - Integration tests
   - Manual testing on Cloud Run

4. **Phase 4** (Day 6-7): Deployment
   - Update deployment scripts
   - Deploy to staging
   - Monitor performance
   - Deploy to production

### 11. Success Metrics

- **Primary**: 95%+ success rate for transcript fetching in production
- **Latency**: < 5 second increase in transcript fetch time
- **Availability**: 99%+ uptime for proxy service
- **Cost**: Stay within $50/month proxy budget

### 12. Rollback Plan

If proxy implementation fails:
1. Set `PROXY_ENABLED=false` in Cloud Run environment
2. Investigate alternative solutions (YouTube API v3, client-side fetching)
3. Consider alternative proxy providers (Bright Data, Oxylabs)

## Appendix A: Alternative Solutions Considered

1. **YouTube Data API v3**: Requires API key, has quota limits, doesn't provide full transcripts
2. **Client-side fetching**: Would require significant architecture changes
3. **Self-hosted proxy**: Maintenance overhead and potential IP blocking
4. **Other proxy services**: Webshare has best track record with youtube-transcript-api

## Appendix B: References

- [youtube-transcript-api Proxy Documentation](https://github.com/jdepoix/youtube-transcript-api#working-around-ip-bans)
- [Webshare API Documentation](https://apidocs.webshare.io/)
- [Webshare Residential Proxies](https://www.webshare.io/residential-proxy)
- [Community Discussion on Proxy Services](https://github.com/jdepoix/youtube-transcript-api/discussions/335)

## Appendix C: Implementation Notes and Learnings

### Initial Implementation Attempt (Dec 2024)

During the initial implementation attempt, several important learnings were discovered:

#### 1. Pydantic Model Constraints
- The `TranscriptTool` class extends Pydantic's `BaseModel`, which doesn't allow arbitrary attributes
- Solution: Use private attributes (prefixed with `_`) for storing proxy configuration
- Example: `self._proxy_config` instead of `self.proxy_config`

#### 2. Testing Challenges
- Direct patching of settings attributes (e.g., `patch('settings.PROXY_ENABLED')`) doesn't work due to how settings are imported
- The settings object is instantiated at module import time, making mocking difficult
- Solution: Mock at the module level where settings is imported: `patch('src.config.proxy_config.settings')`

#### 3. Webshare Proxy Endpoint Format
- Webshare uses a specific proxy endpoint format: `http://username:password@p.webshare.io:80`
- The proxy configuration needs to be properly formatted for the requests library
- The youtube-transcript-api has built-in WebshareProxyConfig support which handles this automatically

#### 4. Health Check Implementation
- Webshare provides an IP check endpoint at `https://ipv4.webshare.io/`
- This can be used to verify proxy connectivity and get the current proxy IP
- Important to handle both WebshareProxyConfig and GenericProxyConfig differently in health checks

#### 5. Tool Initialization Pattern
- Tools are instantiated at module level (e.g., `fetch_transcript = FetchTranscriptTool()`)
- This means proxy configuration is determined at import time, not runtime
- Consider lazy initialization or factory pattern for dynamic proxy configuration

### Recommended Implementation Approach

1. **Research current best practices**: Use web search and context7 to get the latest Webshare API documentation, youtube-transcript-api proxy patterns, and Google Cloud Run deployment practices
2. **Start with minimal changes**: Only modify the exact points where YouTube API calls are made
3. **Use environment-based configuration**: Let Cloud Run environment variables control proxy usage
4. **Implement comprehensive logging**: Log proxy usage, failures, and fallback attempts
5. **Create isolated proxy module**: Keep proxy logic separate from business logic
6. **Test incrementally**: Test proxy connection before integrating with transcript fetching

### Important: Always Check Latest Documentation

Before implementing, always use the following resources to ensure you have the most current information:
- **Web Search**: Search for latest Webshare proxy implementation examples, API changes, and community solutions
- **Context7**: Use context7 to get up-to-date patterns for:
  - youtube-transcript-api proxy implementation
  - FastAPI proxy integration patterns
  - Google Cloud Run environment variable best practices
  - pytest mocking patterns for Pydantic settings
- **Official Docs**: Check for any updates to Webshare API, youtube-transcript-api, or Google Cloud Run documentation

### Future Considerations

1. **Dynamic proxy switching**: Ability to switch between proxy providers without code changes
2. **Proxy pool management**: Rotate through multiple proxy credentials for better reliability
3. **Metrics collection**: Track proxy success rates, response times, and costs
4. **Graceful degradation**: Implement multiple fallback strategies (different proxies, regions, etc.)
