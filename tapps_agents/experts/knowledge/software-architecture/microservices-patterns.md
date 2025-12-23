# Microservices Patterns

## Overview

Microservices architecture breaks applications into small, independent services. This guide covers microservices patterns for HomeIQ's 30-service architecture and similar distributed systems.

## Core Principles

### Service Independence

- **Deploy Independently:** Each service can be deployed separately
- **Technology Diversity:** Services can use different technologies
- **Data Isolation:** Each service owns its data
- **Failure Isolation:** Service failures don't cascade

### Service Communication

- **Synchronous:** HTTP/REST, gRPC
- **Asynchronous:** Message queues, event streaming
- **Hybrid:** Combine both patterns as needed

## Service Design Patterns

### Pattern 1: Domain-Driven Design (DDD)

**Bounded Contexts:**
- Each microservice represents a bounded context
- Clear domain boundaries
- Independent data models

**Example for HomeIQ:**
```
services/
  ├── sensor-ingestion/      # Sensor data domain
  ├── device-intelligence/   # Device AI domain
  ├── energy-monitoring/     # Energy domain
  └── user-management/       # User domain
```

### Pattern 2: API Gateway Pattern

**Single Entry Point:**
- All client requests go through gateway
- Routes to appropriate services
- Handles cross-cutting concerns (auth, rate limiting)

**Implementation:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# API Gateway routes
@app.get("/api/sensors")
async def get_sensors():
    # Route to sensor service
    response = await http_client.get("http://sensor-service:8000/sensors")
    return response.json()

@app.get("/api/devices")
async def get_devices():
    # Route to device service
    response = await http_client.get("http://device-service:8000/devices")
    return response.json()
```

### Pattern 3: Service Discovery

**Pattern:** Services discover each other dynamically

**Client-Side Discovery:**
```python
from consul import Consul

class ServiceDiscovery:
    def __init__(self):
        self.consul = Consul()
    
    def get_service_url(self, service_name: str) -> str:
        """Get service URL from service discovery."""
        services = self.consul.agent.services()
        service = services.get(service_name)
        if service:
            return f"http://{service['Address']}:{service['Port']}"
        raise ServiceNotFoundError(f"Service {service_name} not found")
```

**Server-Side Discovery:**
- Load balancer queries service registry
- Routes requests to available instances

### Pattern 4: Circuit Breaker

**Prevent Cascading Failures:**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_service(service_url: str, endpoint: str):
    """Call service with circuit breaker."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{service_url}/{endpoint}")
        return response.json()
```

## Communication Patterns

### Pattern 1: Synchronous HTTP

**REST API Communication:**
```python
import httpx

class ServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_data(self, endpoint: str):
        """Get data from service."""
        response = await self.client.get(f"{self.base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()
    
    async def post_data(self, endpoint: str, data: dict):
        """Post data to service."""
        response = await self.client.post(
            f"{self.base_url}/{endpoint}",
            json=data
        )
        response.raise_for_status()
        return response.json()
```

### Pattern 2: Asynchronous Events

**Event-Driven Communication:**
```python
from pydantic import BaseModel
import asyncio

class EventPublisher:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
    
    async def publish_event(self, event_type: str, data: dict):
        """Publish event to message broker."""
        # Implementation depends on broker (RabbitMQ, Kafka, etc.)
        pass

class EventSubscriber:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
        self.handlers = {}
    
    def register_handler(self, event_type: str, handler):
        """Register event handler."""
        self.handlers[event_type] = handler
    
    async def listen(self):
        """Listen for events."""
        # Implementation depends on broker
        pass
```

### Pattern 3: Request-Reply Pattern

**Synchronous Request with Async Reply:**
```python
import asyncio
from uuid import uuid4

class RequestReplyClient:
    def __init__(self, message_broker):
        self.broker = message_broker
        self.pending_requests = {}
    
    async def send_request(self, service: str, request: dict, timeout: int = 30):
        """Send request and wait for reply."""
        request_id = str(uuid4())
        request["request_id"] = request_id
        
        # Create future for reply
        future = asyncio.Future()
        self.pending_requests[request_id] = future
        
        # Publish request
        await self.broker.publish(f"{service}.request", request)
        
        # Wait for reply
        try:
            reply = await asyncio.wait_for(future, timeout=timeout)
            return reply
        except asyncio.TimeoutError:
            del self.pending_requests[request_id]
            raise TimeoutError("Request timed out")
```

## Data Management Patterns

### Pattern 1: Database per Service

**Each Service Owns Its Database:**
```
service-a/
  └── database: postgres (service_a_db)

service-b/
  └── database: mongodb (service_b_db)

service-c/
  └── database: influxdb (service_c_db)
```

**Benefits:**
- Technology independence
- Data isolation
- Independent scaling

### Pattern 2: Saga Pattern

**Distributed Transactions:**
```python
class SagaOrchestrator:
    def __init__(self):
        self.steps = []
        self.compensations = []
    
    def add_step(self, step_func, compensation_func):
        """Add saga step with compensation."""
        self.steps.append(step_func)
        self.compensations.append(compensation_func)
    
    async def execute(self):
        """Execute saga with compensation on failure."""
        completed_steps = []
        try:
            for step in self.steps:
                result = await step()
                completed_steps.append(step)
            return result
        except Exception as e:
            # Compensate completed steps in reverse order
            for step in reversed(completed_steps):
                idx = self.steps.index(step)
                await self.compensations[idx]()
            raise
```

### Pattern 3: CQRS (Command Query Responsibility Segregation)

**Separate Read and Write Models:**
```python
# Write model (command)
class DeviceCommandService:
    async def create_device(self, device_data: dict):
        """Create device (write)."""
        # Write to primary database
        device = await self.device_repo.create(device_data)
        # Publish event
        await self.event_publisher.publish("device.created", device)
        return device

# Read model (query)
class DeviceQueryService:
    async def get_device(self, device_id: str):
        """Get device (read)."""
        # Read from read-optimized database
        return await self.device_read_repo.get(device_id)
```

## Deployment Patterns

### Pattern 1: Container per Service

**Each Service in Own Container:**
```dockerfile
# Dockerfile for service
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 2: Service Mesh

**Service-to-Service Communication:**
- Istio, Linkerd, Consul Connect
- Handles load balancing, retries, circuit breaking
- Observability and security

## HomeIQ-Specific Patterns

### Pattern 1: 30-Service Architecture

**Service Organization:**
```
services/
  ├── core/
  │   ├── api-gateway/
  │   ├── user-management/
  │   └── authentication/
  ├── ingestion/
  │   ├── websocket-ingestion/
  │   ├── mqtt-ingestion/
  │   └── sensor-ingestion/
  ├── processing/
  │   ├── device-intelligence/
  │   ├── energy-analysis/
  │   └── anomaly-detection/
  └── storage/
      ├── time-series-db/
      └── metadata-db/
```

### Pattern 2: Event-Driven Sensor Processing

**Sensor Data Flow:**
```
Sensor → WebSocket Ingestion → Event Bus → Processing Services
```

**Implementation:**
```python
# Ingestion service publishes events
await event_publisher.publish("sensor.data", {
    "device_id": "sensor_001",
    "value": 72.5,
    "timestamp": "2026-01-15T10:30:00Z"
})

# Processing services subscribe
@event_subscriber.subscribe("sensor.data")
async def handle_sensor_data(event):
    # Process sensor data
    await process_sensor_reading(event.data)
```

## Best Practices

### 1. Service Boundaries

- **Single Responsibility:** One service, one purpose
- **Loose Coupling:** Minimize dependencies
- **High Cohesion:** Related functionality together

### 2. API Design

- **Versioning:** Use API versioning
- **Backward Compatibility:** Maintain compatibility
- **Documentation:** OpenAPI/Swagger specs

### 3. Error Handling

- **Graceful Degradation:** Handle service failures
- **Retry Logic:** Exponential backoff
- **Circuit Breakers:** Prevent cascading failures

### 4. Observability

- **Logging:** Structured logging
- **Metrics:** Service metrics
- **Tracing:** Distributed tracing

### 5. Security

- **Authentication:** Service-to-service auth
- **Authorization:** Role-based access
- **Encryption:** TLS for communication

## References

- [Microservices Patterns](https://microservices.io/patterns/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Service Mesh](https://istio.io/latest/docs/concepts/what-is-istio/)

