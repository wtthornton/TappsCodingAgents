# External API Integration Patterns

## Overview

This guide covers patterns for integrating with external APIs (OpenWeatherMap, WattTime, etc.) used in HomeIQ and similar applications.

## Core Patterns

### Pattern 1: API Client with Retry

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class ExternalAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get(self, endpoint: str, params: dict = None):
        """GET request with retry."""
        try:
            response = await self.client.get(
                f"{self.base_url}/{endpoint}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                # Retry on server errors
                raise
            # Don't retry on client errors
            raise
    
    async def close(self):
        """Close client."""
        await self.client.aclose()
```

### Pattern 2: Rate Limiting

```python
import asyncio
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = timedelta(seconds=time_window)
        self.requests = deque()
    
    async def acquire(self):
        """Acquire rate limit token."""
        now = datetime.now()
        
        # Remove old requests
        while self.requests and now - self.requests[0] > self.time_window:
            self.requests.popleft()
        
        # Check if limit reached
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] + self.time_window - now).total_seconds()
            await asyncio.sleep(wait_time)
            return await self.acquire()
        
        # Add current request
        self.requests.append(now)

class RateLimitedAPIClient:
    def __init__(self, base_url: str, api_key: str, rate_limit: RateLimiter):
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.client = httpx.AsyncClient()
    
    async def get(self, endpoint: str):
        """GET request with rate limiting."""
        await self.rate_limit.acquire()
        response = await self.client.get(
            f"{self.base_url}/{endpoint}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        return response.json()
```

### Pattern 3: Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta
import asyncio

class CachedAPIClient:
    def __init__(self, base_url: str, api_key: str, cache_ttl: int = 3600):
        self.base_url = base_url
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.client = httpx.AsyncClient()
    
    async def get(self, endpoint: str, use_cache: bool = True):
        """GET request with caching."""
        cache_key = endpoint
        
        # Check cache
        if use_cache and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                return cached_data
        
        # Fetch from API
        response = await self.client.get(
            f"{self.base_url}/{endpoint}",
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        response.raise_for_status()
        data = response.json()
        
        # Cache result
        if use_cache:
            self.cache[cache_key] = (data, datetime.now())
        
        return data
```

## HomeIQ-Specific Patterns

### Pattern 1: OpenWeatherMap Integration

```python
class OpenWeatherMapClient:
    def __init__(self, api_key: str):
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.api_key = api_key
        self.client = httpx.AsyncClient()
        self.rate_limit = RateLimiter(max_requests=60, time_window=60)  # 60/min
    
    async def get_weather(self, lat: float, lon: float):
        """Get weather data."""
        await self.rate_limit.acquire()
        response = await self.client.get(
            f"{self.base_url}/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "imperial"
            }
        )
        response.raise_for_status()
        return response.json()
```

### Pattern 2: WattTime Integration

```python
class WattTimeClient:
    def __init__(self, username: str, password: str):
        self.base_url = "https://api.watttime.org/v2"
        self.username = username
        self.password = password
        self.token = None
        self.client = httpx.AsyncClient()
    
    async def authenticate(self):
        """Authenticate and get token."""
        response = await self.client.get(
            f"{self.base_url}/login",
            auth=(self.username, self.password)
        )
        response.raise_for_status()
        self.token = response.json()["token"]
    
    async def get_grid_data(self, region: str):
        """Get grid data."""
        if not self.token:
            await self.authenticate()
        
        response = await self.client.get(
            f"{self.base_url}/data",
            params={"region": region},
            headers={"Authorization": f"Bearer {self.token}"}
        )
        response.raise_for_status()
        return response.json()
```

### Pattern 3: Multiple External APIs

```python
class ExternalAPIManager:
    def __init__(self):
        self.weather_client = OpenWeatherMapClient(api_key="...")
        self.watttime_client = WattTimeClient(username="...", password="...")
        self.airnow_client = AirNowClient(api_key="...")
    
    async def get_all_data(self, location: dict):
        """Get data from all external APIs."""
        results = {}
        
        # Fetch from all APIs concurrently
        tasks = [
            self.weather_client.get_weather(location["lat"], location["lon"]),
            self.watttime_client.get_grid_data(location["region"]),
            self.airnow_client.get_air_quality(location["lat"], location["lon"])
        ]
        
        weather, grid, air_quality = await asyncio.gather(*tasks, return_exceptions=True)
        
        results["weather"] = weather if not isinstance(weather, Exception) else None
        results["grid"] = grid if not isinstance(grid, Exception) else None
        results["air_quality"] = air_quality if not isinstance(air_quality, Exception) else None
        
        return results
```

## OAuth2-Based External APIs

Many SaaS APIs (Zoho, Okta, Salesforce, Site24x7) use OAuth2 refresh-token flows for long-lived API access without user re-authentication.

### Pattern: OAuth2 Refresh-Token Client

```python
import os
import time
from typing import Any

import requests


class OAuth2ExternalAPIClient:
    """
    OAuth2-based external API client using refresh-token flow.
    
    This pattern is used by many SaaS APIs that require long-term access
    without user re-authentication. See api-security-patterns.md for detailed
    OAuth2 refresh-token implementation patterns.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        api_base_url: str,
        token_url: str,
        timeout_s: int = 30,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.api_base_url = api_base_url.rstrip("/")
        self.token_url = token_url
        self.timeout_s = timeout_s
        
        self._access_token: str | None = None
        self._access_token_expiry_epoch: float = 0.0
    
    def _refresh_access_token(self) -> str:
        """Exchange refresh_token for access_token."""
        resp = requests.post(
            self.token_url,
            data={
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
            },
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        payload = resp.json()
        
        if "access_token" not in payload:
            raise RuntimeError("Token response missing access_token")
        
        access_token = payload["access_token"]
        expires_in = payload.get("expires_in_sec", payload.get("expires_in", 3600))
        
        # Refresh proactively (60 seconds before expiry)
        self._access_token_expiry_epoch = time.time() + int(expires_in) - 60
        self._access_token = access_token
        return access_token
    
    def _get_access_token(self) -> str:
        """Get valid access token, refreshing if necessary."""
        if self._access_token and time.time() < self._access_token_expiry_epoch:
            return self._access_token
        return self._refresh_access_token()
    
    def _headers(self) -> dict[str, str]:
        """Get HTTP headers for authenticated requests."""
        token = self._get_access_token()
        # Note: Some APIs use custom headers (e.g. Zoho uses "Zoho-oauthtoken")
        # See api-security-patterns.md for custom header patterns
        return {
            "Authorization": f"Bearer {token}",  # Standard OAuth2
            "Accept": "application/json",
        }
    
    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make authenticated GET request."""
        url = f"{self.api_base_url}/{path.lstrip('/')}"
        resp = requests.get(
            url,
            headers=self._headers(),
            params=params,
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        return resp.json()
    
    def post(
        self, path: str, data: dict[str, Any] | None = None, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make authenticated POST request."""
        url = f"{self.api_base_url}/{path.lstrip('/')}"
        resp = requests.post(
            url,
            headers=self._headers(),
            data=data,
            json=json,
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        return resp.json()
```

### Examples

#### Zoho/Site24x7
```python
client = OAuth2ExternalAPIClient(
    client_id=os.environ["SITE24X7_CLIENT_ID"],
    client_secret=os.environ["SITE24X7_CLIENT_SECRET"],
    refresh_token=os.environ["SITE24X7_REFRESH_TOKEN"],
    api_base_url="https://www.site24x7.com/api",
    token_url="https://accounts.zoho.com/oauth/v2/token",
)

# Note: Zoho uses custom header "Zoho-oauthtoken" instead of "Bearer"
# Override _headers() method for custom header format:
def _headers(self) -> dict[str, str]:
    token = self._get_access_token()
    return {
        "Authorization": f"Zoho-oauthtoken {token}",  # Custom header
        "Accept": "application/json",
    }

status = client.get("/current_status")
```

#### Okta
```python
client = OAuth2ExternalAPIClient(
    client_id=os.environ["OKTA_CLIENT_ID"],
    client_secret=os.environ["OKTA_CLIENT_SECRET"],
    refresh_token=os.environ["OKTA_REFRESH_TOKEN"],
    api_base_url=f"https://{org}.okta.com/api/v1",
    token_url=f"https://{org}.okta.com/oauth2/v1/token",
)

users = client.get("/users")
```

#### Salesforce
```python
client = OAuth2ExternalAPIClient(
    client_id=os.environ["SALESFORCE_CLIENT_ID"],
    client_secret=os.environ["SALESFORCE_CLIENT_SECRET"],
    refresh_token=os.environ["SALESFORCE_REFRESH_TOKEN"],
    api_base_url="https://yourinstance.salesforce.com/services/data/v58.0",
    token_url="https://login.salesforce.com/services/oauth2/token",
)

accounts = client.get("/sobjects/Account")
```

### Best Practices for OAuth2 External APIs

1. **Token Refresh Strategies:**
   - **Proactive refresh:** Refresh 60 seconds before expiry to avoid race conditions
   - **Reactive refresh:** Refresh only when token expires (simpler but may cause request failures)
   - **Recommendation:** Use proactive refresh for production systems

2. **Error Handling for Token Expiry:**
   ```python
   def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
       """Make request with automatic token refresh on 401."""
       try:
           return self._make_request("GET", path, params=params)
       except requests.HTTPError as e:
           if e.response.status_code == 401:
               # Token expired, refresh and retry once
               self._access_token = None  # Force refresh
               return self._make_request("GET", path, params=params)
           raise
   ```

3. **Multi-Region Support:**
   ```python
   # Some providers have different endpoints for different regions
   REGIONS = {
       "us": {
           "api_base_url": "https://www.site24x7.com/api",
           "token_url": "https://accounts.zoho.com/oauth/v2/token",
       },
       "eu": {
           "api_base_url": "https://www.site24x7.eu/api",
           "token_url": "https://accounts.zoho.eu/oauth/v2/token",
       },
   }
   
   client = OAuth2ExternalAPIClient(
       ...,
       **REGIONS["eu"],  # Use EU endpoints
   )
   ```

4. **Custom Header Formats:**
   - Some APIs (Zoho, GitHub) use non-standard auth headers
   - Make header format configurable or override `_headers()` method
   - See `api-security-patterns.md` section "Custom Authentication Headers" for details

5. **Secure Storage:**
   - Never hardcode credentials
   - Use environment variables or secret managers
   - Rotate refresh tokens regularly

## Error Handling

### Pattern 1: API Error Handling

```python
class APIError(Exception):
    pass

class RateLimitError(APIError):
    pass

class AuthenticationError(APIError):
    pass

async def handle_api_error(response: httpx.Response):
    """Handle API errors."""
    if response.status_code == 429:
        raise RateLimitError("Rate limit exceeded")
    elif response.status_code == 401:
        raise AuthenticationError("Authentication failed")
    elif response.status_code >= 500:
        raise APIError(f"Server error: {response.status_code}")
    else:
        response.raise_for_status()
```

## Best Practices

### 1. Use Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
```

### 2. Implement Rate Limiting

```python
rate_limit = RateLimiter(max_requests=60, time_window=60)
```

### 3. Cache Responses

```python
cache_ttl = 3600  # 1 hour
```

### 4. Handle Errors Gracefully

```python
try:
    data = await api_client.get(endpoint)
except RateLimitError:
    # Handle rate limit
    pass
except AuthenticationError:
    # Re-authenticate
    pass
```

### 5. Use Async for Concurrent Requests

```python
results = await asyncio.gather(*tasks)
```

## References

- [HTTPX Documentation](https://www.python-httpx.org/)
- [Tenacity Retry Library](https://tenacity.readthedocs.io/)
- [API Rate Limiting](https://en.wikipedia.org/wiki/Rate_limiting)

