# Containerization Best Practices

## Overview

Containerization packages applications with dependencies into portable, isolated units. This guide covers Docker best practices, multi-stage builds, container patterns, and production considerations.

## Docker Best Practices

### Image Optimization

**Multi-Stage Builds:**
```dockerfile
# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/dist ./dist
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

**Benefits:**
- Smaller final images
- No build tools in production
- Better security (fewer layers)

### Layer Caching

**Order Layers by Change Frequency:**
```dockerfile
# Dependencies (change less frequently)
COPY package.json package-lock.json ./
RUN npm ci

# Source code (changes frequently)
COPY . .
```

**Use .dockerignore:**
```
node_modules
.git
.env
*.log
dist
```

### Security Best Practices

**Non-Root User:**
```dockerfile
FROM node:18-alpine
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001
USER nodejs
```

**Minimal Base Images:**
- Use `-alpine` variants
- Avoid unnecessary packages
- Keep images small

**Scan for Vulnerabilities:**
```bash
docker scan myimage:latest
```

## Container Patterns

### Sidecar Pattern

**Separate Concerns:**
```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: app
      image: myapp:latest
    - name: proxy
      image: nginx:alpine
      # Sidecar handles logging, monitoring, etc.
```

### Init Containers

**Setup Before Main Container:**
```yaml
spec:
  initContainers:
    - name: init-db
      image: busybox
      command: ['sh', '-c', 'until nc -z db 5432; do sleep 1; done']
  containers:
    - name: app
      image: myapp:latest
```

### Ambassador Pattern

**Proxy Service Calls:**
- Container proxies requests to external services
- Handles retries, circuit breaking
- Simplifies application code

## Production Considerations

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Health Checks

**Liveness Probe:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
```

**Readiness Probe:**
```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Logging Strategy

**Write to stdout/stderr:**
- Applications log to stdout
- Container runtime captures
- Aggregated by logging infrastructure

### Secret Management

**Use Secrets:**
```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: password
```

## Best Practices Summary

1. **Use multi-stage builds** for smaller images
2. **Order layers** by change frequency
3. **Run as non-root** user
4. **Set resource limits** to prevent resource exhaustion
5. **Implement health checks** for reliability
6. **Use .dockerignore** to reduce build context
7. **Scan images** for vulnerabilities
8. **Keep images small** with minimal base images
9. **Log to stdout** for aggregation
10. **Use secrets** for sensitive data

