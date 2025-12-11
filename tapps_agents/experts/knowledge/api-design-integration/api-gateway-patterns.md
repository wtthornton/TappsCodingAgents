# API Gateway Patterns

## Overview

An API Gateway is a single entry point for all client requests, handling routing, authentication, rate limiting, and other cross-cutting concerns. It simplifies client-server communication and provides a unified interface to microservices.

## Core Responsibilities

### 1. Request Routing

**Route to Backend Services:**
```yaml
routes:
  - path: /api/users
    service: user-service
    method: GET
  - path: /api/orders
    service: order-service
    method: POST
  - path: /api/products/*
    service: product-service
```

### 2. Authentication & Authorization

**Validate tokens and forward requests:**
```python
def authenticate_request(request):
    token = request.headers.get('Authorization')
    if not validate_token(token):
        return 401, "Unauthorized"
    
    user = decode_token(token)
    request.headers['X-User-ID'] = user.id
    return None, None
```

### 3. Rate Limiting

**Enforce rate limits:**
```python
def check_rate_limit(request):
    key = get_client_key(request)
    if not rate_limiter.is_allowed(key):
        return 429, "Rate limit exceeded"
    return None, None
```

### 4. Request Transformation

**Modify requests before forwarding:**
- Add headers
- Transform payloads
- Convert protocols
- Aggregate requests

### 5. Response Aggregation

**Combine multiple service responses:**
```python
async def get_user_dashboard(user_id):
    user = await user_service.get_user(user_id)
    orders = await order_service.get_orders(user_id)
    preferences = await pref_service.get_preferences(user_id)
    
    return {
        "user": user,
        "orders": orders,
        "preferences": preferences
    }
```

## Gateway Patterns

### 1. Backend for Frontend (BFF)

**Different Gateways per Client Type:**
```
Mobile App → Mobile BFF Gateway → Services
Web App → Web BFF Gateway → Services
Admin → Admin BFF Gateway → Services
```

**Benefits:**
- Optimized for each client
- Reduces over-fetching
- Simplified client logic

### 2. API Aggregation

**Combine Multiple Services:**
```python
@app.route('/api/user-profile/<user_id>')
async def get_user_profile(user_id):
    # Aggregate from multiple services
    profile = await aggregate([
        user_service.get_user(user_id),
        order_service.get_recent_orders(user_id),
        notification_service.get_unread_count(user_id)
    ])
    return profile
```

### 3. Protocol Translation

**HTTP to gRPC:**
```python
@app.route('/api/users', methods=['POST'])
async def create_user():
    request_data = request.json
    
    # Convert HTTP JSON to gRPC
    grpc_request = user_pb2.CreateUserRequest(
        name=request_data['name'],
        email=request_data['email']
    )
    
    # Call gRPC service
    response = user_service_stub.CreateUser(grpc_request)
    
    # Convert gRPC to HTTP JSON
    return jsonify({
        "id": response.id,
        "name": response.name
    })
```

## Implementation Patterns

### Kong Gateway

**Configuration:**
```yaml
services:
  - name: user-service
    url: http://user-service:8000
    routes:
      - name: user-route
        paths:
          - /api/users
    plugins:
      - name: rate-limiting
        config:
          minute: 100
      - name: jwt
        config:
          secret_is_base64: false
```

### Envoy Proxy

**Configuration:**
```yaml
static_resources:
  listeners:
    - address:
        socket_address:
          address: 0.0.0.0
          port_value: 8080
      filter_chains:
        - filters:
            - name: envoy.http_connection_manager
              config:
                route_config:
                  virtual_hosts:
                    - name: api
                      routes:
                        - match:
                            prefix: "/api/users"
                          route:
                            cluster: user_service
```

### NGINX Gateway

**Configuration:**
```nginx
upstream user_service {
    server user-service-1:8000;
    server user-service-2:8000;
}

server {
    listen 80;
    
    location /api/users {
        proxy_pass http://user_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Cross-Cutting Concerns

### Logging

**Log all requests:**
```python
@app.before_request
def log_request():
    logger.info("Request",
        method=request.method,
        path=request.path,
        client_ip=request.remote_addr,
        user_id=request.headers.get('X-User-ID')
    )
```

### Metrics

**Track metrics:**
```python
from prometheus_client import Counter, Histogram

request_count = Counter('gateway_requests_total', ...)
request_duration = Histogram('gateway_request_duration_seconds', ...)

@app.before_request
def track_request():
    request.start_time = time.time()

@app.after_request
def track_response(response):
    duration = time.time() - request.start_time
    request_count.inc()
    request_duration.observe(duration)
    return response
```

### Caching

**Cache responses:**
```python
from functools import lru_cache
from datetime import timedelta

@cache.cached(timeout=300)
@app.route('/api/users/<user_id>')
def get_user(user_id):
    return forward_to_service('user-service', f'/users/{user_id}')
```

### Circuit Breaker

**Protect downstream services:**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_user_service(endpoint):
    return requests.get(f'http://user-service{endpoint}')
```

## Security Patterns

### JWT Validation

**Validate tokens:**
```python
import jwt

def validate_jwt(token):
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256']
        )
        return payload
    except jwt.InvalidTokenError:
        return None
```

### API Key Validation

**Check API keys:**
```python
def validate_api_key(api_key):
    key_record = db.get_api_key(api_key)
    if not key_record or not key_record.is_active:
        return None
    return key_record.user_id
```

### IP Whitelisting

**Restrict by IP:**
```python
ALLOWED_IPS = ['192.168.1.0/24', '10.0.0.0/8']

def is_ip_allowed(ip):
    return any(ipaddress.ip_address(ip) in ipaddress.ip_network(cidr) 
               for cidr in ALLOWED_IPS)
```

## Best Practices

1. **Single entry point:** All clients through gateway
2. **Stateless design:** Don't store session state
3. **Fail fast:** Circuit breakers for downstream services
4. **Cache appropriately:** Reduce load on services
5. **Monitor everything:** Logs, metrics, traces
6. **Handle errors gracefully:** Meaningful error responses
7. **Version APIs:** Support multiple API versions
8. **Security first:** Authenticate and authorize all requests
9. **Rate limit:** Protect from abuse
10. **Document APIs:** Clear documentation for clients

