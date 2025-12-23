# Service Communication Patterns

## Overview

This guide covers inter-service communication patterns for microservices architectures, including HTTP, gRPC, and event-driven communication.

## Communication Styles

### Synchronous Communication

**HTTP/REST:**
- Request-response pattern
- Simple to implement
- Can cause cascading failures
- Use for real-time queries

**gRPC:**
- High performance
- Type-safe
- Streaming support
- Use for internal services

### Asynchronous Communication

**Message Queues:**
- Decoupled services
- Better fault tolerance
- Eventual consistency
- Use for event processing

**Event Streaming:**
- Real-time event processing
- High throughput
- Use for analytics, logging

## HTTP/REST Patterns

### Pattern 1: Service Client with Retry

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class ServiceClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
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
    
    async def post(self, endpoint: str, data: dict):
        """POST request."""
        response = await self.client.post(
            f"{self.base_url}/{endpoint}",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close client."""
        await self.client.aclose()
```

### Pattern 2: Service Discovery Integration

```python
class DiscoverableServiceClient:
    def __init__(self, service_name: str, service_discovery):
        self.service_name = service_name
        self.discovery = service_discovery
        self.client = httpx.AsyncClient()
    
    async def get_service_url(self) -> str:
        """Get service URL from discovery."""
        return await self.discovery.get_service_url(self.service_name)
    
    async def request(self, method: str, endpoint: str, **kwargs):
        """Make request with service discovery."""
        base_url = await self.get_service_url()
        response = await self.client.request(
            method,
            f"{base_url}/{endpoint}",
            **kwargs
        )
        response.raise_for_status()
        return response.json()
```

### Pattern 3: Circuit Breaker Pattern

```python
from circuitbreaker import circuit

class ResilientServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def call_service(self, endpoint: str):
        """Call service with circuit breaker."""
        response = await self.client.get(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()
```

## gRPC Patterns

### Pattern 1: gRPC Client

```python
import grpc
from grpc import aio

class GRPCServiceClient:
    def __init__(self, service_stub, server_address: str):
        self.stub = service_stub
        self.server_address = server_address
        self.channel = None
    
    async def connect(self):
        """Connect to gRPC server."""
        self.channel = aio.insecure_channel(self.server_address)
        self.stub = self.stub(self.channel)
    
    async def call(self, method_name: str, request):
        """Call gRPC method."""
        method = getattr(self.stub, method_name)
        response = await method(request)
        return response
    
    async def close(self):
        """Close channel."""
        if self.channel:
            await self.channel.close()
```

### Pattern 2: gRPC Streaming

```python
async def stream_data(stub, request):
    """Stream data from gRPC service."""
    async for response in stub.StreamData(request):
        yield response
```

## Event-Driven Patterns

### Pattern 1: Event Publisher

```python
from pydantic import BaseModel
from typing import Any

class Event(BaseModel):
    event_type: str
    data: dict[str, Any]
    timestamp: str
    source: str

class EventPublisher:
    def __init__(self, broker):
        self.broker = broker
    
    async def publish(self, event_type: str, data: dict, source: str):
        """Publish event."""
        event = Event(
            event_type=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
            source=source
        )
        await self.broker.publish(event_type, event.dict())
```

### Pattern 2: Event Subscriber

```python
class EventSubscriber:
    def __init__(self, broker):
        self.broker = broker
        self.handlers = {}
    
    def register_handler(self, event_type: str, handler):
        """Register event handler."""
        self.handlers[event_type] = handler
    
    async def subscribe(self, event_type: str):
        """Subscribe to event type."""
        async for event in self.broker.subscribe(event_type):
            if event_type in self.handlers:
                await self.handlers[event_type](event)
```

### Pattern 3: Event Sourcing

```python
class EventStore:
    def __init__(self, storage):
        self.storage = storage
    
    async def append(self, stream_id: str, events: list[Event]):
        """Append events to stream."""
        await self.storage.append(stream_id, events)
    
    async def get_stream(self, stream_id: str):
        """Get event stream."""
        return await self.storage.get_stream(stream_id)
```

## HomeIQ-Specific Patterns

### Pattern 1: Sensor Data Pipeline

```
Sensor → WebSocket Service → Event Bus → Processing Services → Storage
```

**Implementation:**
```python
# WebSocket service publishes events
await event_publisher.publish("sensor.data", {
    "device_id": "sensor_001",
    "value": 72.5,
    "timestamp": "2026-01-15T10:30:00Z"
})

# Processing services subscribe
@event_subscriber.subscribe("sensor.data")
async def process_sensor_data(event):
    # Process and store
    await storage_service.store(event.data)
```

### Pattern 2: Service-to-Service Calls

```python
# Device service calls user service
user_client = ServiceClient("http://user-service:8000")
user = await user_client.get(f"/users/{user_id}")

# Device service calls sensor service
sensor_client = ServiceClient("http://sensor-service:8000")
sensors = await sensor_client.get(f"/devices/{device_id}/sensors")
```

## Best Practices

### 1. Timeout Configuration

```python
# Set appropriate timeouts
client = httpx.AsyncClient(timeout=30.0)  # 30 seconds
```

### 2. Retry Strategy

```python
# Exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
```

### 3. Circuit Breaker

```python
# Prevent cascading failures
@circuit(failure_threshold=5, recovery_timeout=60)
```

### 4. Health Checks

```python
async def health_check(service_url: str) -> bool:
    """Check service health."""
    try:
        response = await client.get(f"{service_url}/health")
        return response.status_code == 200
    except Exception:
        return False
```

### 5. Service Discovery

- Use service registry (Consul, etcd)
- Implement client-side discovery
- Cache service locations

## References

- [gRPC Documentation](https://grpc.io/docs/)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [Service Communication Patterns](https://microservices.io/patterns/communication-style/)

