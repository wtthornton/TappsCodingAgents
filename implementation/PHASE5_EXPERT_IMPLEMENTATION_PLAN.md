# Phase 5: Expert Framework Enhancement - High Priority Experts

**Date:** January 2026  
**Status:** ✅ **COMPLETE**  
**Version:** 2.2.0  
**Target Release:** January 2026  
**Actual Duration:** Completed

> **Status Note (2025-12-11):** This file is a historical snapshot.  
> **Canonical status:** See `implementation/IMPLEMENTATION_STATUS.md`.

---

## Executive Summary

This plan details the implementation of **Phase 5** expert enhancements, adding 4 critical built-in experts that address modern software development needs identified through comprehensive analysis. These experts fill critical gaps in production operations, infrastructure, data management, and API design capabilities.

### Key Objectives

1. **Implement 4 new high-priority built-in experts** - Observability, API Design, Cloud Infrastructure, Database
2. **Comprehensive knowledge bases** - ~40 new knowledge files covering modern best practices
3. **Agent integration** - Enhanced support for ops, architect, designer, and implementer agents
4. **2025 modern patterns** - Cloud-native, observability-first, API-first design principles
5. **Production-ready** - Focus on operational excellence and real-world production scenarios

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Phase 5.1: Observability & Monitoring Expert](#2-phase-51-observability--monitoring-expert)
3. [Phase 5.2: API Design & Integration Expert](#3-phase-52-api-design--integration-expert)
4. [Phase 5.3: Cloud & Infrastructure Expert](#4-phase-53-cloud--infrastructure-expert)
5. [Phase 5.4: Database & Data Management Expert](#5-phase-54-database--data-management-expert)
6. [Phase 5.5: Integration & Testing](#6-phase-55-integration--testing)
7. [Phase 5.6: Documentation & Release](#7-phase-56-documentation--release)

---

## 1. Architecture Overview

### 1.1 Expert Registry Expansion

Phase 5 adds 4 new built-in experts to the existing 11 experts, bringing the total to **15 built-in technical experts**:

```
tapps_agents/experts/builtin_registry.py
├── Existing Experts (11)
│   ├── expert-security ✅
│   ├── expert-performance ✅
│   ├── expert-testing ✅
│   ├── expert-data-privacy ✅
│   ├── expert-accessibility ✅
│   ├── expert-user-experience ✅
│   ├── expert-ai-frameworks ✅
│   ├── expert-code-quality ✅
│   ├── expert-software-architecture ✅
│   ├── expert-devops ✅
│   └── expert-documentation ✅
│
└── Phase 5 Experts (4) 🆕
    ├── expert-observability ⏳
    ├── expert-api-design ⏳
    ├── expert-cloud-infrastructure ⏳
    └── expert-database ⏳
```

### 1.2 Knowledge Base Structure

```
tapps_agents/experts/knowledge/
├── security/              # ✅ Existing
├── performance/          # ✅ Existing
├── testing/              # ✅ Existing
├── data-privacy-compliance/  # ✅ Existing
├── accessibility/        # ✅ Existing
├── user-experience/      # ✅ Existing
│
├── observability-monitoring/  # 🆕 Phase 5.1
│   ├── distributed-tracing.md
│   ├── metrics-and-monitoring.md
│   ├── logging-strategies.md
│   ├── apm-tools.md
│   ├── slo-sli-sla.md
│   ├── alerting-patterns.md
│   ├── observability-best-practices.md
│   └── open-telemetry.md
│
├── api-design-integration/   # 🆕 Phase 5.2
│   ├── restful-api-design.md
│   ├── graphql-patterns.md
│   ├── grpc-best-practices.md
│   ├── api-versioning.md
│   ├── rate-limiting.md
│   ├── api-gateway-patterns.md
│   ├── api-security-patterns.md
│   └── contract-testing.md
│
├── cloud-infrastructure/     # 🆕 Phase 5.3
│   ├── cloud-native-patterns.md
│   ├── containerization.md
│   ├── kubernetes-patterns.md
│   ├── infrastructure-as-code.md
│   ├── serverless-architecture.md
│   ├── multi-cloud-strategies.md
│   ├── cost-optimization.md
│   └── disaster-recovery.md
│
└── database-data-management/ # 🆕 Phase 5.4
    ├── database-design.md
    ├── sql-optimization.md
    ├── nosql-patterns.md
    ├── data-modeling.md
    ├── migration-strategies.md
    ├── scalability-patterns.md
    ├── backup-and-recovery.md
    └── acid-vs-cap.md
```

### 1.3 Agent Integration Points

| Expert | Primary Agents | Secondary Agents | Consultation Domains |
|--------|---------------|------------------|---------------------|
| **Observability** | ops, reviewer | architect, tester | Production monitoring, debugging, performance analysis |
| **API Design** | designer, architect | implementer, tester | API contracts, integration patterns, versioning |
| **Cloud Infrastructure** | architect, ops | implementer, reviewer | Infrastructure design, deployment, scaling |
| **Database** | architect, designer | implementer, ops | Data modeling, query optimization, migration |

---

## 2. Phase 5.1: Observability & Monitoring Expert

**Duration:** 2 weeks  
**Priority:** 🔴 High  
**Status:** ⏳ Planning

### 2.0 Scope & Boundaries

**Focus Areas:**
- Instrumentation for observability (OpenTelemetry)
- Distributed tracing patterns
- Metrics collection and aggregation
- Logging strategies and log aggregation
- APM (Application Performance Monitoring) tools
- SLO/SLI/SLA definitions
- Alerting patterns and on-call practices

**Boundaries (Complementary Experts):**
- **Performance Expert**: Uses observability data to optimize performance, focuses on performance tuning based on metrics

**Key Distinction:** Observability Expert focuses on **how to observe and monitor systems**, while Performance Expert focuses on **how to optimize systems based on what you observe**.

### 2.1 Expert Configuration

**File:** `tapps_agents/experts/builtin_registry.py` (MODIFY)

```python
# Add to BUILTIN_EXPERTS list
ExpertConfigModel(
    expert_id="expert-observability",
    expert_name="Observability & Monitoring Expert",
    primary_domain="observability-monitoring",
    rag_enabled=True,
    fine_tuned=False,
)
```

**File:** `tapps_agents/experts/builtin_registry.py` (MODIFY TECHNICAL_DOMAINS)

```python
TECHNICAL_DOMAINS: Set[str] = {
    # ... existing domains ...
    "observability-monitoring",  # 🆕
}
```

### 2.2 Knowledge Base Creation

**Directory:** `tapps_agents/experts/knowledge/observability-monitoring/`

#### 2.2.1 Files to Create (8 files)

1. **`distributed-tracing.md`** - OpenTelemetry, Jaeger, Zipkin patterns
2. **`metrics-and-monitoring.md`** - Prometheus, StatsD, Datadog patterns
3. **`logging-strategies.md`** - Structured logging, log aggregation
4. **`apm-tools.md`** - Application Performance Monitoring tools
5. **`slo-sli-sla.md`** - Service Level Objectives, Indicators, Agreements
6. **`alerting-patterns.md`** - Alert design, on-call practices
7. **`observability-best-practices.md`** - Three pillars (logs, metrics, traces)
8. **`open-telemetry.md`** - OpenTelemetry standards and instrumentation

#### 2.2.2 Knowledge Base Content Outline

**Example:** `distributed-tracing.md`

```markdown
# Distributed Tracing Best Practices

## Overview

Distributed tracing provides visibility into requests as they flow through microservices, helping identify bottlenecks, errors, and performance issues.

## Key Concepts

### OpenTelemetry Standard

OpenTelemetry is the open standard for observability, providing:
- Unified instrumentation APIs
- Vendor-neutral instrumentation
- Automatic and manual instrumentation support

### Trace Components

- **Trace**: Complete request lifecycle
- **Span**: Individual operation within a trace
- **Span Context**: Propagation metadata
- **Baggage**: Custom key-value pairs

## Best Practices

### 1. Instrumentation Strategy

- **Auto-instrumentation**: Use libraries when available
- **Manual instrumentation**: For custom operations
- **Sampling**: Balance detail vs. cost

### 2. Span Naming

```python
# Good: Clear, hierarchical naming
span.set_name("user_service.get_user_profile")

# Bad: Generic names
span.set_name("function_call")
```

### 3. Context Propagation

- Use W3C Trace Context standard
- Propagate across service boundaries
- Include correlation IDs

### 4. Span Attributes

Add useful metadata:
- Service name
- Operation name
- Error flags
- Custom business context

## Common Patterns

### Service Mesh Integration

- Istio, Linkerd provide automatic tracing
- Zero-code tracing for HTTP/gRPC
- Consistent trace propagation

### Error Tracking

```python
span.record_exception(exception)
span.set_attribute("error", True)
span.set_status(StatusCode.ERROR)
```

## Tools & Frameworks

- **Jaeger**: Distributed tracing backend
- **Zipkin**: Open-source distributed tracing
- **DataDog APM**: Commercial tracing solution
- **New Relic**: Full-stack observability
```

### 2.3 Agent Integration

**File:** `tapps_agents/agents/ops/agent.py` (MODIFY)

Add observability expert consultation:

```python
from ...experts.agent_integration import ExpertSupportMixin

class OpsAgent(BaseAgent, ExpertSupportMixin):
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
        await self._initialize_expert_support(project_root)
    
    async def monitor_system(self, service: str):
        """Consult observability expert for monitoring recommendations."""
        result = await self._consult_builtin_expert(
            query=f"Recommend monitoring strategy for {service}",
            domain="observability-monitoring"
        )
        
        if result:
            return {
                "monitoring_strategy": result.weighted_answer,
                "recommended_tools": self._extract_tools(result),
                "slo_recommendations": self._extract_slos(result)
            }
```

**File:** `tapps_agents/agents/reviewer/agent.py` (MODIFY)

Add observability checks to code review:

```python
async def review_observability(self, code: str):
    """Review code for observability best practices."""
    result = await self._consult_builtin_expert(
        query=f"Review this code for observability:\n{code}",
        domain="observability-monitoring"
    )
    
    return result.weighted_answer if result else []
```

---

## 3. Phase 5.2: API Design & Integration Expert

**Duration:** 2 weeks  
**Priority:** 🔴 High  
**Status:** ⏳ Planning

### 3.0 Scope & Boundaries

**Focus Areas:**
- API structure and design patterns (REST, GraphQL, gRPC)
- API versioning strategies
- API gateway patterns
- API contracts and testing
- API integration patterns

**Boundaries (Complementary Experts):**
- **Performance Expert**: Handles API optimization, caching, response time tuning
- **Software Architecture Expert**: Handles high-level API strategy, API boundaries in system architecture
- **Security Expert**: Handles API security vulnerabilities, authentication/authorization details

**Key Distinction:** API Design Expert focuses on **how to structure and design APIs**, not on optimizing their performance or making high-level architectural decisions.

### 3.1 Expert Configuration

**File:** `tapps_agents/experts/builtin_registry.py` (MODIFY)

```python
ExpertConfigModel(
    expert_id="expert-api-design",
    expert_name="API Design & Integration Expert",
    primary_domain="api-design-integration",
    rag_enabled=True,
    fine_tuned=False,
)
```

```python
TECHNICAL_DOMAINS.add("api-design-integration")  # 🆕
```

### 3.2 Knowledge Base Creation

**Directory:** `tapps_agents/experts/knowledge/api-design-integration/`

#### 3.2.1 Files to Create (8 files)

1. **`restful-api-design.md`** - REST principles, OpenAPI/Swagger, endpoint structure
2. **`graphql-patterns.md`** - GraphQL schema design, resolvers, query optimization
3. **`grpc-best-practices.md`** - Protocol Buffers, service definitions, streaming patterns
4. **`api-versioning.md`** - Versioning strategies (URL, header, content), deprecation
5. **`rate-limiting.md`** - Rate limiting patterns as design concern, throttling strategies
6. **`api-gateway-patterns.md`** - API gateway architecture, routing, aggregation patterns
7. **`api-security-patterns.md`** - API security design (OAuth2, JWT patterns), API keys
8. **`contract-testing.md`** - API contract testing, Pact, consumer-driven contracts

**Note:** For API performance optimization, caching strategies, and response time tuning, see Performance Expert. For API security vulnerabilities and detailed authentication/authorization, see Security Expert.

#### 3.2.2 Knowledge Base Content Outline

**Example:** `restful-api-design.md`

```markdown
# RESTful API Design Best Practices

## REST Principles

### Resource-Based Design

- Resources are nouns, not verbs
- Use HTTP methods for actions
- URLs represent resources, not operations

### HTTP Methods

- **GET**: Retrieve resource (idempotent, safe)
- **POST**: Create resource (not idempotent)
- **PUT**: Update/replace resource (idempotent)
- **PATCH**: Partial update (idempotent)
- **DELETE**: Remove resource (idempotent)

### Status Codes

- **2xx**: Success
  - 200 OK
  - 201 Created
  - 204 No Content
- **4xx**: Client errors
  - 400 Bad Request
  - 401 Unauthorized
  - 404 Not Found
  - 409 Conflict
- **5xx**: Server errors
  - 500 Internal Server Error
  - 503 Service Unavailable

## API Design Patterns

### Resource Naming

```yaml
# Good: Hierarchical, consistent
GET    /users
GET    /users/{id}
GET    /users/{id}/posts
POST   /users/{id}/posts

# Bad: Verbs, inconsistent
GET    /getUser
POST   /createUser
GET    /user_posts/{userId}
```

### Query Parameters

- Filtering: `?status=active&role=admin`
- Pagination: `?page=1&limit=20`
- Sorting: `?sort=created_at:desc`
- Field selection: `?fields=id,name,email`

### Response Formats

```json
{
  "data": [...],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100
    }
  },
  "links": {
    "self": "/users?page=1",
    "next": "/users?page=2"
  }
}
```

## OpenAPI/Swagger Specification

### Benefits

- API documentation
- Code generation
- Contract testing
- Interactive API explorer

### Example

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
```

## Versioning Strategies

### URL Versioning

```
/api/v1/users
/api/v2/users
```

### Header Versioning

```
Accept: application/vnd.api+json;version=2
```

### Content Negotiation

```
Accept: application/json;v=2
```

## Error Handling

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ]
  }
}
```

## Security

- Authentication: OAuth2, JWT
- Authorization: RBAC, ABAC
- Rate limiting: Prevent abuse
- Input validation: Sanitize all inputs
- HTTPS: Always use TLS
```

### 3.3 Agent Integration

**File:** `tapps_agents/agents/designer/agent.py` (MODIFY)

Add API design expert consultation:

```python
from ...experts.agent_integration import ExpertSupportMixin

class DesignerAgent(BaseAgent, ExpertSupportMixin):
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
        await self._initialize_expert_support(project_root)
    
    async def design_api(self, requirements: str):
        """Design API with expert guidance."""
        result = await self._consult_builtin_expert(
            query=f"Design REST API for: {requirements}",
            domain="api-design-integration"
        )
        
        if result:
            return {
                "api_design": result.weighted_answer,
                "endpoints": self._extract_endpoints(result),
                "best_practices": self._extract_practices(result)
            }
```

---

## 4. Phase 5.3: Cloud & Infrastructure Expert

**Duration:** 2-3 weeks  
**Priority:** 🔴 High  
**Status:** ⏳ Planning

### 4.0 Scope & Boundaries

**Focus Areas:**
- Cloud-native patterns and principles (12-factor app)
- Containerization (Docker) and orchestration (Kubernetes)
- Infrastructure as Code (Terraform, CloudFormation, Pulumi)
- Serverless architecture patterns
- Multi-cloud strategies
- Cloud cost optimization
- Disaster recovery and backup strategies

**Boundaries (Complementary Experts):**
- **DevOps Expert**: Handles CI/CD pipelines, testing automation, deployment workflows
- **Software Architecture Expert**: Handles general microservices patterns, service boundaries (technology-agnostic)
- **Performance Expert**: Handles resource optimization based on monitoring data

**Key Distinction:** Cloud Infrastructure Expert focuses on **infrastructure design and deployment in cloud environments**, not on CI/CD workflows or general architectural patterns.

### 4.1 Expert Configuration

**File:** `tapps_agents/experts/builtin_registry.py` (MODIFY)

```python
ExpertConfigModel(
    expert_id="expert-cloud-infrastructure",
    expert_name="Cloud & Infrastructure Expert",
    primary_domain="cloud-infrastructure",
    rag_enabled=True,
    fine_tuned=False,
)
```

```python
TECHNICAL_DOMAINS.add("cloud-infrastructure")  # 🆕
```

### 4.2 Knowledge Base Creation

**Directory:** `tapps_agents/experts/knowledge/cloud-infrastructure/`

#### 4.2.1 Files to Create (8 files)

1. **`cloud-native-patterns.md`** - 12-factor app, cloud-native principles
2. **`containerization.md`** - Docker best practices, multi-stage builds
3. **`kubernetes-patterns.md`** - K8s deployment, services, ingress, operators
4. **`infrastructure-as-code.md`** - Terraform, CloudFormation, Pulumi, IaC patterns
5. **`serverless-architecture.md`** - Lambda, Functions, event-driven patterns
6. **`multi-cloud-strategies.md`** - Multi-cloud patterns, portability, vendor lock-in
7. **`cost-optimization.md`** - Cloud cost management, right-sizing, cost allocation
8. **`disaster-recovery.md`** - Backup strategies, DR plans, RTO/RPO

**Note:** For CI/CD pipeline design and testing automation, see DevOps Expert. For general microservices patterns and service boundaries, see Software Architecture Expert.

#### 4.2.2 Knowledge Base Content Outline

**Example:** `containerization.md`

```markdown
# Containerization Best Practices

## Docker Best Practices

### Image Optimization

```dockerfile
# Multi-stage builds for smaller images
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
USER node
CMD ["node", "server.js"]
```

### Layer Caching

- Order layers by change frequency
- Copy dependencies before source code
- Use .dockerignore

### Security

- Use non-root users
- Scan images for vulnerabilities
- Keep base images updated
- Minimize attack surface

## Container Patterns

### Sidecar Pattern

```
┌─────────────────┐
│  Main Container │
│  (Application)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Sidecar │
    │ (Proxy) │
    └─────────┘
```

### Init Containers

- Run before main container
- Setup, configuration, dependency checks

## Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://db:5432/app
    depends_on:
      - db
  
  db:
    image: postgres:15-alpine
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

## Production Considerations

- Resource limits (CPU, memory)
- Health checks
- Logging strategy
- Secret management
- Networking
```

### 4.3 Agent Integration

**File:** `tapps_agents/agents/architect/agent.py` (MODIFY)

Add cloud infrastructure expert consultation:

```python
from ...experts.agent_integration import ExpertSupportMixin

class ArchitectAgent(BaseAgent, ExpertSupportMixin):
    async def activate(self, project_root: Optional[Path] = None):
        await super().activate(project_root)
        await self._initialize_expert_support(project_root)
    
    async def design_infrastructure(self, requirements: str):
        """Design cloud infrastructure with expert guidance."""
        result = await self._consult_builtin_expert(
            query=f"Design cloud infrastructure for: {requirements}",
            domain="cloud-infrastructure"
        )
        
        if result:
            return {
                "infrastructure_design": result.weighted_answer,
                "recommended_patterns": self._extract_patterns(result),
                "cost_considerations": self._extract_costs(result)
            }
```

---

## 5. Phase 5.4: Database & Data Management Expert

**Duration:** 2 weeks  
**Priority:** 🔴 High  
**Status:** ⏳ Planning

### 5.0 Scope & Boundaries

**Focus Areas:**
- Database design and schema modeling
- Data normalization and denormalization strategies
- Database architecture (ACID vs CAP theorem)
- Database type selection (SQL vs NoSQL)
- Migration strategies
- Scalability patterns (sharding, replication)
- Backup and recovery strategies

**Boundaries (Complementary Experts):**
- **Performance Expert**: Handles query optimization, indexing for performance, connection pooling
- **Data Privacy Expert**: Handles data privacy compliance, GDPR, encryption for privacy

**Key Distinction:** Database Expert focuses on **database design and architecture**, while Performance Expert focuses on **optimizing existing database queries and operations**.

### 5.1 Expert Configuration

**File:** `tapps_agents/experts/builtin_registry.py` (MODIFY)

```python
ExpertConfigModel(
    expert_id="expert-database",
    expert_name="Database & Data Management Expert",
    primary_domain="database-data-management",
    rag_enabled=True,
    fine_tuned=False,
)
```

```python
TECHNICAL_DOMAINS.add("database-data-management")  # 🆕
```

### 5.2 Knowledge Base Creation

**Directory:** `tapps_agents/experts/knowledge/database-data-management/`

#### 5.2.1 Files to Create (8 files)

1. **`database-design.md`** - Normalization, schema design, entity relationships
2. **`sql-optimization.md`** - SQL query structure, indexing strategies (design perspective)
3. **`nosql-patterns.md`** - Document, key-value, column, graph DBs, use cases
4. **`data-modeling.md`** - Entity relationships, data patterns, modeling techniques
5. **`migration-strategies.md`** - Schema migrations, data migrations, versioning
6. **`scalability-patterns.md`** - Sharding, replication, caching strategies
7. **`backup-and-recovery.md`** - Backup strategies, point-in-time recovery, RTO/RPO
8. **`acid-vs-cap.md`** - Transaction guarantees, consistency models, database selection

**Note:** For query performance optimization, connection pooling, and performance tuning of existing queries, see Performance Expert's `database-performance.md`. For data privacy compliance and encryption, see Data Privacy Expert.

#### 5.2.2 Knowledge Base Content Outline

**Example:** `sql-optimization.md`

```markdown
# SQL Query Optimization

## Indexing Strategies

### When to Index

- Frequently queried columns
- JOIN columns
- WHERE clause columns
- ORDER BY columns
- Foreign keys

### Index Types

- **B-tree**: Default, balanced tree
- **Hash**: Equality lookups
- **GIN**: Full-text search
- **GiST**: Geometric data

### Composite Indexes

```sql
-- Good: Covers multiple query patterns
CREATE INDEX idx_user_email_status ON users(email, status);

-- Query uses index
SELECT * FROM users WHERE email = ? AND status = ?;

-- Also works (uses part of index)
SELECT * FROM users WHERE email = ?;
```

## Query Optimization

### EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE customer_id = 123
  AND status = 'completed'
ORDER BY created_at DESC;
```

### Common Issues

#### N+1 Queries

```python
# Bad: N+1 queries
users = User.objects.all()
for user in users:
    print(user.profile.name)  # Query per user

# Good: Eager loading
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.name)  # Single query
```

#### Missing WHERE Clauses

```sql
-- Bad: Full table scan
SELECT * FROM orders WHERE DATE(created_at) = '2025-01-01';

-- Good: Index-friendly
SELECT * FROM orders 
WHERE created_at >= '2025-01-01' 
  AND created_at < '2025-01-02';
```

## Normalization vs Denormalization

### Normalization (OLTP)

- Eliminate redundancy
- Ensure data integrity
- Optimize for writes

### Denormalization (OLAP)

- Pre-computed aggregations
- Optimize for reads
- Accept redundancy

## Connection Pooling

```python
# Connection pool configuration
pool_size = 10
max_overflow = 20
pool_timeout = 30
```

## Partitioning

### Range Partitioning

```sql
CREATE TABLE orders (
    id SERIAL,
    created_at TIMESTAMP,
    ...
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2025_q1 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
```

## Database-Specific Optimizations

### PostgreSQL

- EXPLAIN ANALYZE
- VACUUM and ANALYZE
- Partial indexes
- Materialized views

### MySQL

- EXPLAIN
- Query cache (deprecated in 8.0)
- Index hints
- Table partitioning
```

### 5.3 Agent Integration

**File:** `tapps_agents/agents/designer/agent.py` (MODIFY)

Add database expert consultation:

```python
async def design_data_model(self, requirements: str):
    """Design data model with expert guidance."""
    result = await self._consult_builtin_expert(
        query=f"Design database schema for: {requirements}",
        domain="database-data-management"
    )
    
    if result:
        return {
            "data_model": result.weighted_answer,
            "normalization_level": self._extract_normalization(result),
            "indexing_strategy": self._extract_indexing(result)
        }
```

---

## 6. Phase 5.5: Integration & Testing

**Duration:** 1-2 weeks  
**Priority:** 🔴 Critical  
**Status:** ⏳ Planning

### 6.1 Unit Tests

**Files to Create:**

- `tests/unit/experts/test_observability_expert.py`
- `tests/unit/experts/test_api_design_expert.py`
- `tests/unit/experts/test_cloud_infrastructure_expert.py`
- `tests/unit/experts/test_database_expert.py`

**Test Coverage Goals:**
- 90%+ code coverage for each expert
- RAG knowledge base retrieval tests
- Consultation result validation
- Weight calculation tests

### 6.2 Integration Tests

**Files to Create:**

- `tests/integration/test_observability_agent_integration.py`
- `tests/integration/test_api_design_agent_integration.py`
- `tests/integration/test_cloud_infrastructure_agent_integration.py`
- `tests/integration/test_database_agent_integration.py`

**Test Scenarios:**

1. Agent consults expert during workflow
2. Expert provides weighted recommendations
3. Knowledge base retrieval works correctly
4. Multiple expert consultation works
5. Fallback behavior works

### 6.3 End-to-End Tests

**Scenarios:**

1. **Observability**: Ops agent requests monitoring strategy
2. **API Design**: Designer agent creates API specification
3. **Cloud Infrastructure**: Architect agent designs infrastructure
4. **Database**: Designer agent creates database schema

### 6.4 Test Examples

```python
# tests/unit/experts/test_observability_expert.py
import pytest
from tapps_agents.experts.builtin_registry import BuiltinExpertRegistry
from tapps_agents.experts.expert_registry import ExpertRegistry

@pytest.mark.asyncio
async def test_observability_expert_consultation():
    """Test observability expert provides recommendations."""
    registry = ExpertRegistry(load_builtin=True)
    
    result = await registry.consult(
        query="Recommend monitoring strategy for microservices",
        domain="observability-monitoring",
        prioritize_builtin=True
    )
    
    assert result is not None
    assert result.confidence > 0.7
    assert "tracing" in result.weighted_answer.lower() or "metrics" in result.weighted_answer.lower()
```

---

## 7. Phase 5.6: Documentation & Release

**Duration:** 1 week  
**Priority:** 🔴 Critical  
**Status:** ⏳ Planning

### 7.1 Documentation Updates

#### 7.1.1 Built-in Experts Guide

**File:** `docs/BUILTIN_EXPERTS_GUIDE.md` (UPDATE)

**Add sections for:**

- Observability & Monitoring Expert
- API Design & Integration Expert
- Cloud & Infrastructure Expert
- Database & Data Management Expert

**Include:**

- Expert use cases
- Knowledge base contents
- Agent integration examples
- Common consultation patterns
- Best practices

#### 7.1.2 API Documentation

**File:** `docs/API.md` (UPDATE)

**Add:**

- Expert registry API updates
- New consultation domains
- Agent integration patterns
- Code examples for each expert

#### 7.1.3 Knowledge Base Guide

**File:** `docs/EXPERT_KNOWLEDGE_BASE_GUIDE.md` (UPDATE)

**Add:**

- Knowledge base structure for Phase 5 experts
- Content guidelines for each domain
- Example knowledge files
- Maintenance guidelines

### 7.2 Release Preparation

#### 7.2.1 Version Bump

**File:** `setup.py` (UPDATE)

```python
version="2.1.0"  # Minor version bump for new experts
```

#### 7.2.2 Changelog

**File:** `CHANGELOG.md` (UPDATE)

```markdown
## [2.1.0] - 2026-Q2

### Added
- Observability & Monitoring Expert (8 knowledge files)
- API Design & Integration Expert (8 knowledge files)
- Cloud & Infrastructure Expert (8 knowledge files)
- Database & Data Management Expert (8 knowledge files)
- Enhanced agent integration for ops, designer, architect agents
- 32 new knowledge base files covering modern software development practices

### Enhanced
- Ops Agent: Observability monitoring recommendations
- Designer Agent: API design and data modeling guidance
- Architect Agent: Cloud infrastructure design patterns
- Reviewer Agent: Observability best practices review

### Changed
- Expert registry now includes 15 built-in experts (was 11)
- Technical domains expanded to 15 domains
```

#### 7.2.3 Migration Guide

**File:** `docs/MIGRATION_GUIDE_2.0.md` (UPDATE)

**Add section:**

```markdown
## Migrating to 2.1.0

### New Experts Available

Phase 5 introduces 4 new built-in experts that are automatically available:

1. **Observability Expert**: Consult for monitoring and observability patterns
2. **API Design Expert**: Consult for API design and integration patterns
3. **Cloud Infrastructure Expert**: Consult for cloud-native patterns
4. **Database Expert**: Consult for database design and optimization

### Using New Experts

```python
# Example: Consult observability expert
result = await registry.consult(
    query="Recommend monitoring strategy",
    domain="observability-monitoring",
    prioritize_builtin=True
)
```
```

---

## 8. Implementation Timeline

### Week 1-2: Phase 5.1 (Observability Expert)
- ✅ Expert configuration
- ✅ Knowledge base creation (8 files)
- ✅ Agent integration (ops, reviewer)
- ✅ Unit tests

### Week 3-4: Phase 5.2 (API Design Expert)
- ✅ Expert configuration
- ✅ Knowledge base creation (8 files)
- ✅ Agent integration (designer, architect)
- ✅ Unit tests

### Week 5-7: Phase 5.3 (Cloud Infrastructure Expert)
- ✅ Expert configuration
- ✅ Knowledge base creation (8 files)
- ✅ Agent integration (architect, ops)
- ✅ Unit tests

### Week 8-9: Phase 5.4 (Database Expert)
- ✅ Expert configuration
- ✅ Knowledge base creation (8 files)
- ✅ Agent integration (designer, architect)
- ✅ Unit tests

### Week 10: Phase 5.5 (Integration & Testing)
- ✅ Integration tests
- ✅ End-to-end tests
- ✅ Performance testing
- ✅ Test coverage validation

### Week 11: Phase 5.6 (Documentation & Release)
- ✅ Documentation updates
- ✅ Changelog
- ✅ Version bump
- ✅ Release preparation

**Total Duration:** 10-11 weeks

---

## 9. Success Criteria

### Functional Requirements

- ✅ All 4 experts registered in builtin_registry
- ✅ All 32 knowledge files created and validated
- ✅ Agent integration working for all target agents
- ✅ RAG retrieval working correctly
- ✅ Weighted consultation working

### Quality Requirements

- ✅ 90%+ unit test coverage for each expert
- ✅ All integration tests passing
- ✅ All end-to-end tests passing
- ✅ Documentation complete and accurate
- ✅ No breaking changes to existing APIs

### Performance Requirements

- ✅ Expert consultation < 2 seconds (with RAG)
- ✅ Knowledge base retrieval < 500ms
- ✅ No memory leaks in expert registry

---

## 10. Risk Mitigation

### Risk 1: Knowledge Base Quality

**Mitigation:**
- Review all knowledge files before implementation
- Validate content accuracy with domain experts
- Include examples and code snippets
- Regular updates based on feedback

### Risk 2: Agent Integration Complexity

**Mitigation:**
- Follow existing ExpertSupportMixin pattern
- Comprehensive testing at each integration point
- Clear documentation for agent developers

### Risk 3: Timeline Overrun

**Mitigation:**
- Incremental implementation (one expert at a time)
- Prioritize knowledge base quality
- Defer non-critical features if needed

---

## 11. Future Enhancements (Post-Phase 5)

### Phase 6: Medium Priority Experts

1. Migration & Modernization Expert
2. Concurrency & Parallelism Expert
3. Internationalization Expert
4. Cost Optimization Expert

### Phase 7: Specialized Experts

1. Event-Driven Architecture Expert
2. GraphQL Expert
3. MLOps Expert
4. Web3 & Blockchain Expert

---

## 12. References

- [OpenTelemetry Documentation](https://opentelemetry.io/)
- [REST API Design Guide](https://restfulapi.net/)
- [12-Factor App Methodology](https://12factor.net/)
- [Database Design Best Practices](https://www.postgresql.org/docs/current/ddl-best-practices.html)
- Existing Expert Framework: `implementation/EXPERT_FRAMEWORK_ENHANCEMENT_PLAN_2025.md`

---

**Document Status:** Planning Complete, Ready for Implementation  
**Last Updated:** January 2026  
**Next Review:** After Phase 5.1 completion

