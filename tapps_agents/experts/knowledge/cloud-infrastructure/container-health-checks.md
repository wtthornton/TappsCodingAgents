# Container Health Checks

## Overview

Health checks ensure containers are running correctly and ready to serve traffic. This guide covers health check patterns for Docker containers and orchestration platforms.

## Docker Health Checks

### Pattern 1: Basic Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**Parameters:**
- `--interval`: Time between checks (default: 30s)
- `--timeout`: Time to wait for response (default: 30s)
- `--start-period`: Grace period on startup (default: 0s)
- `--retries`: Consecutive failures before unhealthy (default: 3)

### Pattern 2: Python Service Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1
```

### Pattern 3: Database Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pg_isready -U postgres || exit 1
```

## Application Health Endpoints

### Pattern 1: FastAPI Health Endpoint

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/health/ready")
async def readiness():
    """Readiness check - service is ready to accept traffic."""
    # Check database connection
    if not await db.is_connected():
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"status": "ready"}

@app.get("/health/live")
async def liveness():
    """Liveness check - service is alive."""
    return {"status": "alive"}
```

### Pattern 2: Comprehensive Health Check

```python
from fastapi import FastAPI, HTTPException
from typing import Dict

app = FastAPI()

@app.get("/health")
async def health() -> Dict[str, any]:
    """Comprehensive health check."""
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check database
    try:
        await db.ping()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "unhealthy"
    
    # Check external services
    try:
        await influxdb_client.ping()
        health_status["checks"]["influxdb"] = "healthy"
    except Exception as e:
        health_status["checks"]["influxdb"] = f"unhealthy: {e}"
        health_status["status"] = "unhealthy"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status
```

## Docker Compose Health Checks

### Pattern 1: Service Health Check

```yaml
services:
  api-service:
    build: ./services/api
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Pattern 2: Dependent Service Health

```yaml
services:
  api-service:
    build: ./services/api
    depends_on:
      database:
        condition: service_healthy
  
  database:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

## Kubernetes Health Checks

### Pattern 1: Liveness Probe

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: api
      image: api:latest
      livenessProbe:
        httpGet:
          path: /health/live
          port: 8000
        initialDelaySeconds: 30
        periodSeconds: 10
        timeoutSeconds: 5
        failureThreshold: 3
```

### Pattern 2: Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Pattern 3: Startup Probe

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 30  # Allow up to 5 minutes for startup
```

## Best Practices

### 1. Separate Liveness and Readiness

- **Liveness:** Service is alive (restart if fails)
- **Readiness:** Service is ready (stop traffic if fails)

### 2. Use Appropriate Timeouts

- **Startup:** Longer timeout for initial startup
- **Runtime:** Shorter timeout for ongoing checks

### 3. Check Dependencies

- Database connections
- External service availability
- Resource availability

### 4. Fail Fast

- Return error immediately if unhealthy
- Don't wait for timeout

### 5. Log Health Check Failures

```python
import logging

logger = logging.getLogger(__name__)

@app.get("/health")
async def health():
    try:
        # Health checks
        return {"status": "healthy"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))
```

## HomeIQ-Specific Patterns

### Pattern 1: Service Health Check

```python
@app.get("/health")
async def health():
    """Service health check."""
    checks = {}
    
    # Check InfluxDB
    try:
        await influxdb_client.ping()
        checks["influxdb"] = "healthy"
    except Exception:
        checks["influxdb"] = "unhealthy"
    
    # Check MQTT broker
    try:
        if mqtt_client.is_connected():
            checks["mqtt"] = "healthy"
        else:
            checks["mqtt"] = "unhealthy"
    except Exception:
        checks["mqtt"] = "unhealthy"
    
    if all(v == "healthy" for v in checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": checks})
```

## References

- [Docker Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Kubernetes Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- [Health Check Patterns](https://microservices.io/patterns/observability/health-check-api.html)

