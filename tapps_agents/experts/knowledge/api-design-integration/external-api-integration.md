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

