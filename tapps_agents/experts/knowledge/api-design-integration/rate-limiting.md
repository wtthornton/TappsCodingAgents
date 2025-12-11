# Rate Limiting Patterns

## Overview

Rate limiting protects APIs from abuse and ensures fair resource usage. It controls the number of requests a client can make within a specific time window.

## Rate Limiting Algorithms

### 1. Fixed Window

**Concept:** Requests allowed per fixed time window

**Example:** 100 requests per minute

**Pros:**
- Simple to implement
- Memory efficient
- Predictable

**Cons:**
- Burst at window boundaries
- Uneven distribution

**Implementation:**
```python
from collections import defaultdict
from datetime import datetime, timedelta

class FixedWindowRateLimiter:
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.windows = defaultdict(int)
        self.window_starts = {}
    
    def is_allowed(self, key):
        now = datetime.now()
        window_start = now.replace(second=0, microsecond=0)
        
        if key not in self.window_starts or \
           window_start > self.window_starts[key] + timedelta(seconds=self.window_seconds):
            # New window
            self.windows[key] = 0
            self.window_starts[key] = window_start
        
        if self.windows[key] >= self.max_requests:
            return False
        
        self.windows[key] += 1
        return True
```

### 2. Sliding Window

**Concept:** Track requests in rolling time window

**Example:** 100 requests in any 60-second window

**Pros:**
- More accurate
- Smoother distribution
- Prevents bursts

**Cons:**
- More memory
- More complex

**Implementation:**
```python
from collections import deque
from datetime import datetime, timedelta

class SlidingWindowRateLimiter:
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    def is_allowed(self, key):
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Remove old requests
        while self.requests[key] and self.requests[key][0] < cutoff:
            self.requests[key].popleft()
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True
```

### 3. Token Bucket

**Concept:** Tokens added at fixed rate, consumed per request

**Example:** 10 tokens/sec, max 100 tokens

**Pros:**
- Allows bursts
- Smooths traffic
- Flexible

**Cons:**
- More complex
- State management

**Implementation:**
```python
from datetime import datetime, timedelta

class TokenBucketRateLimiter:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = defaultdict(lambda: capacity)
        self.last_refill = defaultdict(datetime.now)
    
    def is_allowed(self, key):
        now = datetime.now()
        elapsed = (now - self.last_refill[key]).total_seconds()
        
        # Refill tokens
        self.tokens[key] = min(
            self.capacity,
            self.tokens[key] + elapsed * self.refill_rate
        )
        self.last_refill[key] = now
        
        if self.tokens[key] >= 1:
            self.tokens[key] -= 1
            return True
        return False
```

### 4. Leaky Bucket

**Concept:** Requests leak out at constant rate

**Example:** Process 10 requests/sec, queue up to 100

**Pros:**
- Smooths output
- Handles bursts
- Predictable rate

**Cons:**
- Queue management
- Memory usage

## Implementation Patterns

### Redis-Based Rate Limiting

**Using Fixed Window:**
```python
import redis
from datetime import datetime

redis_client = redis.Redis()

def rate_limit(key, max_requests, window_seconds):
    now = datetime.now()
    window = int(now.timestamp() / window_seconds)
    redis_key = f"ratelimit:{key}:{window}"
    
    current = redis_client.incr(redis_key)
    if current == 1:
        redis_client.expire(redis_key, window_seconds)
    
    return current <= max_requests
```

**Using Sliding Window with Sorted Sets:**
```python
def sliding_window_rate_limit(key, max_requests, window_seconds):
    now = datetime.now().timestamp()
    cutoff = now - window_seconds
    
    redis_key = f"ratelimit:{key}"
    
    # Remove old entries
    redis_client.zremrangebyscore(redis_key, 0, cutoff)
    
    # Count current requests
    current = redis_client.zcard(redis_key)
    
    if current < max_requests:
        redis_client.zadd(redis_key, {str(now): now})
        redis_client.expire(redis_key, window_seconds)
        return True
    
    return False
```

### Middleware Pattern

**Flask Example:**
```python
from flask import request, g, jsonify
from functools import wraps

def rate_limit(max_requests, window_seconds):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = get_rate_limit_key()  # IP, user ID, API key
            
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                return jsonify({
                    "error": "Rate limit exceeded"
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/api/users')
@rate_limit(max_requests=100, window_seconds=60)
def get_users():
    return jsonify(users=[...])
```

### Header Response

**Rate Limit Headers:**
```python
def add_rate_limit_headers(response, remaining, reset_time):
    response.headers['X-RateLimit-Limit'] = str(max_requests)
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['X-RateLimit-Reset'] = str(int(reset_time.timestamp()))
    return response
```

**RFC 6585 Standard Headers:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1642233600
```

## Rate Limit Keys

### By IP Address

**Simple but Limited:**
```python
def get_rate_limit_key():
    return request.remote_addr
```

### By API Key

**Better for APIs:**
```python
def get_rate_limit_key():
    api_key = request.headers.get('X-API-Key')
    return f"apikey:{api_key}"
```

### By User ID

**For Authenticated Users:**
```python
def get_rate_limit_key():
    user_id = g.current_user.id
    return f"user:{user_id}"
```

### Composite Keys

**Multiple Factors:**
```python
def get_rate_limit_key():
    user_id = g.current_user.id if g.current_user else None
    endpoint = request.endpoint
    return f"{user_id}:{endpoint}"
```

## Tiered Rate Limits

### Different Limits per Tier

**Free Tier:**
```python
FREE_TIER_LIMITS = {
    'requests_per_minute': 60,
    'requests_per_hour': 1000,
    'requests_per_day': 10000
}
```

**Premium Tier:**
```python
PREMIUM_TIER_LIMITS = {
    'requests_per_minute': 600,
    'requests_per_hour': 100000,
    'requests_per_day': 1000000
}
```

**Implementation:**
```python
def get_rate_limits(user_tier):
    limits = {
        'free': FREE_TIER_LIMITS,
        'premium': PREMIUM_TIER_LIMITS
    }.get(user_tier, FREE_TIER_LIMITS)
    
    return limits

def check_rate_limit(user, endpoint):
    limits = get_rate_limits(user.tier)
    
    for window, max_requests in limits.items():
        if not rate_limiter.is_allowed(
            f"{user.id}:{endpoint}",
            max_requests,
            parse_window(window)
        ):
            return False
    return True
```

## Error Responses

### Standard 429 Response

**Format:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "retry_after": 60
  }
}
```

**Implementation:**
```python
@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded",
            "retry_after": error.retry_after
        }
    }), 429
```

## Best Practices

1. **Choose appropriate algorithm:** Sliding window for accuracy
2. **Use Redis for distributed:** Shared state across instances
3. **Set reasonable limits:** Balance protection and usability
4. **Include rate limit headers:** Inform clients of limits
5. **Return 429 status:** Standard HTTP status for rate limits
6. **Include Retry-After:** Tell clients when to retry
7. **Log rate limit hits:** Monitor for abuse patterns
8. **Tier limits appropriately:** Different limits per user tier
9. **Whitelist if needed:** Exempt certain keys/IPs
10. **Test thoroughly:** Ensure limits work as expected

## Common Patterns

### Per-Endpoint Limits

```python
ENDPOINT_LIMITS = {
    '/api/users': {'max': 100, 'window': 60},
    '/api/orders': {'max': 50, 'window': 60},
    '/api/reports': {'max': 10, 'window': 300},
}
```

### Burst Protection

```python
# Allow bursts but limit sustained rate
BURST_LIMIT = 20  # Immediate burst
SUSTAINED_LIMIT = 100  # Per minute
```

### Adaptive Rate Limiting

```python
def adaptive_rate_limit(user):
    # Increase limit for good users
    if user.reputation_score > 0.95:
        return PREMIUM_LIMITS
    elif user.reputation_score > 0.8:
        return STANDARD_LIMITS
    else:
        return REDUCED_LIMITS
```

## Tools

### Open Source

- **Redis:** Distributed rate limiting
- **nginx rate limiting:** Built-in module
- **Kong:** API gateway with rate limiting
- **Envoy:** Service mesh with rate limiting

### Commercial

- **CloudFlare:** DDoS protection and rate limiting
- **AWS API Gateway:** Built-in throttling
- **Azure API Management:** Rate limit policies

