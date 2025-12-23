# Docker Compose Patterns

## Overview

Docker Compose orchestrates multi-container applications. This guide covers Docker Compose patterns for HomeIQ's 30-service architecture and similar microservices deployments.

## Basic Patterns

### Pattern 1: Service Definition

```yaml
version: '3.8'

services:
  api-gateway:
    build: ./services/api-gateway
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    depends_on:
      - user-service
      - device-service
    networks:
      - homeiq-network

  user-service:
    build: ./services/user-management
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/users
    depends_on:
      - db
    networks:
      - homeiq-network

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=users
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - homeiq-network

networks:
  homeiq-network:
    driver: bridge

volumes:
  db-data:
```

### Pattern 2: Service Dependencies

```yaml
services:
  service-a:
    depends_on:
      - service-b
      - service-c
    # Service A waits for B and C to be healthy

  service-b:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Pattern 3: Health Checks

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

## HomeIQ-Specific Patterns

### Pattern 1: 30-Service Architecture

```yaml
version: '3.8'

services:
  # Core Services
  api-gateway:
    build: ./services/api-gateway
    ports:
      - "8000:8000"
    depends_on:
      - user-service
      - device-service
      - sensor-service
  
  user-service:
    build: ./services/user-management
    environment:
      - DATABASE_URL=postgresql://user:pass@user-db:5432/users
    depends_on:
      - user-db
  
  # Ingestion Services
  websocket-ingestion:
    build: ./services/websocket-ingestion
    environment:
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - influxdb
  
  mqtt-ingestion:
    build: ./services/mqtt-ingestion
    environment:
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - influxdb
  
  # Processing Services
  device-intelligence:
    build: ./services/device-intelligence
    environment:
      - INFLUXDB_URL=http://influxdb:8086
    depends_on:
      - influxdb
  
  # Storage Services
  influxdb:
    image: influxdb:2.7
    ports:
      - "8086:8086"
    volumes:
      - influxdb-data:/var/lib/influxdb2
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=admin123
      - DOCKER_INFLUXDB_INIT_ORG=homeiq
      - DOCKER_INFLUXDB_INIT_BUCKET=homeiq

networks:
  default:
    driver: bridge

volumes:
  influxdb-data:
  user-db-data:
```

### Pattern 2: Service Groups

```yaml
services:
  # Ingestion Group
  websocket-ingestion:
    build: ./services/websocket-ingestion
    networks:
      - ingestion-network
  
  mqtt-ingestion:
    build: ./services/mqtt-ingestion
    networks:
      - ingestion-network
  
  # Processing Group
  device-intelligence:
    build: ./services/device-intelligence
    networks:
      - processing-network
    depends_on:
      - websocket-ingestion
      - mqtt-ingestion

networks:
  ingestion-network:
  processing-network:
```

## Best Practices

### 1. Use Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 2. Set Resource Limits

```yaml
services:
  api-service:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### 3. Use Environment Variables

```yaml
services:
  api-service:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}
    env_file:
      - .env
```

### 4. Volume Management

```yaml
services:
  database:
    volumes:
      - db-data:/var/lib/postgresql/data
      # Named volume for persistence

volumes:
  db-data:
    driver: local
```

### 5. Network Isolation

```yaml
services:
  frontend:
    networks:
      - frontend-network
  
  backend:
    networks:
      - backend-network
      - frontend-network  # Can access frontend

networks:
  frontend-network:
  backend-network:
```

## Common Anti-Patterns

### 1. Missing Health Checks

```yaml
# BAD: No health check
services:
  api-service:
    build: ./api

# GOOD: With health check
services:
  api-service:
    build: ./api
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
```

### 2. Hardcoded Dependencies

```yaml
# BAD: Hardcoded service URLs
environment:
  - USER_SERVICE_URL=http://user-service:8000

# GOOD: Use service names (Docker DNS)
environment:
  - USER_SERVICE_URL=http://user-service:8000  # Service name resolves
```

### 3. No Resource Limits

```yaml
# BAD: No limits
services:
  api-service:
    build: ./api

# GOOD: With limits
services:
  api-service:
    build: ./api
    deploy:
      resources:
        limits:
          memory: 512M
```

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Compose Best Practices](https://docs.docker.com/compose/best-practices/)

