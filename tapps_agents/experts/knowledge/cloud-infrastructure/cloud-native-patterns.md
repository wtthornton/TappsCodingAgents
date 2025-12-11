# Cloud-Native Patterns

## Overview

Cloud-native applications are designed to take advantage of cloud computing delivery models, focusing on scalability, resilience, and operational efficiency.

## The Twelve-Factor App

### 1. Codebase
- One codebase tracked in version control
- Many deploys (dev, staging, prod)
- Single source of truth

### 2. Dependencies
- Explicitly declare and isolate dependencies
- Never rely on system-wide packages
- Use dependency manifests (requirements.txt, package.json)

### 3. Config
- Store config in environment variables
- Separate config from code
- No hardcoded credentials

### 4. Backing Services
- Treat backing services as attached resources
- Database, cache, queue as external resources
- Easily swappable

### 5. Build, Release, Run
- Strictly separate build, release, and run stages
- Build once, run anywhere
- Immutable releases

### 6. Processes
- Execute as stateless processes
- Share nothing between processes
- Horizontal scalability

### 7. Port Binding
- Export services via port binding
- Self-contained, no external web server dependency
- Application owns its port

### 8. Concurrency
- Scale via process model
- Stateless processes enable horizontal scaling
- Process types for different workloads

### 9. Disposability
- Maximize robustness with fast startup and graceful shutdown
- Shutdown gracefully on SIGTERM
- Handle crashes gracefully

### 10. Dev/Prod Parity
- Keep development, staging, and production as similar as possible
- Same backing services
- Same dependencies

### 11. Logs
- Treat logs as event streams
- Write to stdout/stderr
- Let infrastructure aggregate

### 12. Admin Processes
- Run admin/management tasks as one-off processes
- Same environment as application
- Example: migrations, data fixes

## Cloud-Native Principles

### Microservices Architecture

**Characteristics:**
- Small, independent services
- Owned by small teams
- Independently deployable
- Loosely coupled

**Benefits:**
- Technology diversity
- Scalability
- Resilience
- Team autonomy

### Containerization

**Benefits:**
- Consistent environments
- Isolation
- Portability
- Resource efficiency

### API-First Design

**Principles:**
- APIs as contracts
- Versioning
- Documentation
- Backward compatibility

### Service Mesh

**Features:**
- Service-to-service communication
- Load balancing
- Security (mTLS)
- Observability

### Serverless Computing

**Characteristics:**
- Event-driven
- Auto-scaling
- Pay-per-use
- No server management

## Design Patterns

### Circuit Breaker

**Prevent cascading failures:**
```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_external_service():
    return requests.get('http://external-service/api')
```

### Bulkhead

**Isolate resources:**
- Separate thread pools
- Isolated database connections
- Resource limits per service

### Retry with Backoff

**Handle transient failures:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_service():
    return requests.get('http://service/api')
```

### Health Checks

**Implement readiness and liveness:**
```python
@app.route('/health/live')
def liveness():
    return {'status': 'alive'}, 200

@app.route('/health/ready')
def readiness():
    if db.is_connected() and cache.is_connected():
        return {'status': 'ready'}, 200
    return {'status': 'not ready'}, 503
```

## Best Practices

1. **Stateless services:** No session state
2. **Externalize configuration:** Environment variables
3. **Health checks:** Liveness and readiness
4. **Graceful shutdown:** Handle SIGTERM
5. **Logging:** Structured logs to stdout
6. **Metrics:** Expose metrics endpoint
7. **Tracing:** Distributed tracing
8. **Security:** Least privilege, secrets management
9. **Observability:** Logs, metrics, traces
10. **Automation:** CI/CD, infrastructure as code

