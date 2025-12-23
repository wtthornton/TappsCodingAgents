# Dockerfile Patterns

## Overview

This guide covers Dockerfile best practices, security patterns, and optimization techniques for HomeIQ and similar production applications.

## Best Practices

### Pattern 1: Multi-Stage Builds

**Separate Build and Runtime:**
```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "main.py"]
```

**Benefits:**
- Smaller final image
- No build tools in production
- Better security

### Pattern 2: Layer Ordering

**Order by Change Frequency:**
```dockerfile
# Dependencies (change less frequently)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code (changes frequently)
COPY . .
```

**Use .dockerignore:**
```
__pycache__
*.pyc
.git
.env
*.log
dist
node_modules
```

### Pattern 3: Non-Root User

**Run as Non-Root:**
```dockerfile
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set ownership
WORKDIR /app
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

CMD ["python", "main.py"]
```

### Pattern 4: Minimal Base Images

**Use Alpine or Distroless:**
```dockerfile
# Alpine (small, but has shell)
FROM python:3.12-alpine

# Distroless (minimal, no shell)
FROM gcr.io/distroless/python3-debian11
```

## Security Patterns

### Pattern 1: No Secrets in Image

**BAD:**
```dockerfile
# NEVER do this
ENV API_KEY=secret123
```

**GOOD:**
```dockerfile
# Use environment variables at runtime
# docker run -e API_KEY=secret123
```

### Pattern 2: Scan for Vulnerabilities

```bash
# Scan image for vulnerabilities
docker scan myimage:latest
```

### Pattern 3: Use Specific Tags

**BAD:**
```dockerfile
FROM python:latest
```

**GOOD:**
```dockerfile
FROM python:3.12-slim
```

### Pattern 4: Update Packages

```dockerfile
FROM python:3.12-slim

# Update packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

## Optimization Patterns

### Pattern 1: Cache Dependencies

```dockerfile
# Copy dependency files first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code last
COPY . .
```

### Pattern 2: Combine RUN Commands

**BAD:**
```dockerfile
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get clean
```

**GOOD:**
```dockerfile
RUN apt-get update && \
    apt-get install -y python3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### Pattern 3: Use BuildKit Cache

```dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.12-slim

# Cache mount for pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

## HomeIQ-Specific Patterns

### Pattern 1: Python Service Dockerfile

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 2: Multi-Service Dockerfile

```dockerfile
# Base image with common dependencies
FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements-common.txt .
RUN pip install --no-cache-dir -r requirements-common.txt

# Service-specific builds
FROM base AS api-service
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt
COPY services/api/ ./services/api/
CMD ["python", "services/api/main.py"]

FROM base AS worker-service
COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt
COPY services/worker/ ./services/worker/
CMD ["python", "services/worker/main.py"]
```

## Common Anti-Patterns

### 1. Running as Root

```dockerfile
# BAD: Running as root
FROM python:3.12-slim
CMD ["python", "main.py"]

# GOOD: Non-root user
FROM python:3.12-slim
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
CMD ["python", "main.py"]
```

### 2. Including Secrets

```dockerfile
# BAD: Secrets in image
ENV DATABASE_PASSWORD=secret123

# GOOD: Use environment variables
# docker run -e DATABASE_PASSWORD=secret123
```

### 3. Not Using .dockerignore

```dockerfile
# BAD: Copies everything
COPY . .

# GOOD: Use .dockerignore
# .dockerignore:
# node_modules
# .git
# *.log
```

### 4. Large Images

```dockerfile
# BAD: Full OS image
FROM ubuntu:latest

# GOOD: Minimal image
FROM python:3.12-alpine
```

## References

- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Security](https://docs.docker.com/engine/security/)

