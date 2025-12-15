# TappsCodingAgents - Part 2: Agent Specifications

**Version:** 2.0  
**Date:** December 14, 2025  
**Status:** Recommended Architecture

---

## Table of Contents

1. [Agent Overview](#agent-overview)
2. [Orchestration Agent](#orchestration-agent)
3. [Background Cloud Agents](#background-cloud-agents)
4. [Foreground Agents](#foreground-agents)
5. [Agent Summary Table](#agent-summary-table)

---

## Agent Overview

This document provides detailed specifications for all 11 agents in the TappsCodingAgents multi-agent architecture.

### Agent Classification

| Category | Count | Agents |
|----------|-------|--------|
| **Orchestration** | 1 | Workflow Orchestration |
| **Background Cloud** | 5 | Quality, Testing, Docs, Ops, Context |
| **Foreground** | 5 | Code, Design, Review, Planning, Enhancement |
| **Total** | 11 | |

---

## Agent 1: Workflow Orchestration Agent

**Type:** Coordination  
**Execution:** Foreground (Always Running)  
**Priority:** Critical

### Responsibilities
- Route tasks to appropriate agents
- Manage dependencies between tasks
- Create and cleanup git worktrees
- Aggregate results from parallel agents
- Resolve conflicts
- Generate final PRs

### Key Capabilities
```python
class OrchestrationAgent:
    def route_task(task):
        """Assign task to most appropriate agent"""
        
    def manage_dependencies(workflow):
        """Build and execute dependency graph"""
        
    def create_worktree(agent_id):
        """Create isolated workspace for agent"""
        
    def aggregate_results(agent_outputs):
        """Combine outputs from multiple agents"""
        
    def resolve_conflicts(changes):
        """Resolve merge conflicts intelligently"""
```

### Runtime
Continuous (coordination layer)

---

## Background Cloud Agents

These run on Cursor's cloud infrastructure.

---

## Agent 2: Quality & Analysis Agent

**Type:** Analysis  
**Execution:** Background Cloud  
**Priority:** Medium  
**Runtime:** 2-10 minutes

### Responsibilities
- Static code analysis (Ruff, ESLint)
- Type checking (mypy, TypeScript)
- Security scanning (Bandit)
- Complexity analysis (Radon)
- Duplication detection (jscpd)
- Dependency audits (pip-audit)

### Output Format
```json
{
  "overall_score": 8.5,
  "metrics": {
    "complexity": {"score": 8.0, "avg": 4.2},
    "security": {"score": 9.0, "vulnerabilities": {"high": 0, "medium": 2}},
    "maintainability": {"score": 8.5, "mi_avg": 72.3},
    "test_coverage": {"score": 7.0, "percentage": 73.5},
    "performance": {"score": 9.0, "issues": 1}
  }
}
```

### Tools Used
- **Python:** Ruff, mypy, Bandit, Radon, pip-audit
- **JavaScript/TypeScript:** ESLint, TypeScript compiler, npm audit
- **Multi-language:** jscpd (duplication)

---

## Agent 3: Testing & Coverage Agent

**Type:** Execution  
**Execution:** Background Cloud  
**Priority:** High  
**Runtime:** 5-30 minutes

### Responsibilities
- Generate unit tests (pytest, jest)
- Generate integration tests
- Execute test suites
- Calculate coverage
- Report failures

### Test Generation Strategy
```python
# For each function:
# 1. Happy path test
# 2. Edge cases (null, empty, boundaries)
# 3. Error cases (exceptions, invalid input)
# 4. Integration tests (if dependencies)
```

### Output Format
```json
{
  "summary": {
    "line_coverage": 87.3,
    "branch_coverage": 82.1,
    "tests_total": 234,
    "tests_passed": 230,
    "tests_failed": 2
  },
  "missing_coverage": [
    {
      "file": "utils.py",
      "lines": [42, 43, 56],
      "reason": "Error handling not tested"
    }
  ]
}
```

---

## Agent 4: Documentation Agent

**Type:** Creation  
**Execution:** Background Cloud  
**Priority:** Low  
**Runtime:** 3-15 minutes

### Responsibilities
- Generate API documentation
- Create/update README.md
- Generate developer guides
- Update CHANGELOG.md
- Create architecture diagrams (Mermaid)
- Generate inline comments

### Output Types
- Markdown files (`.md`)
- Mermaid diagrams (`.mermaid`)
- API reference docs
- Code examples

### Example Output
```markdown
# API Documentation: UserService

## create_user(user_data: UserCreate) -> User

Creates a new user in the system.

**Parameters:**
- user_data: User creation data

**Returns:**
- User: Created user object

**Raises:**
- DuplicateEmailError: Email already exists
- ValidationError: Invalid data

**Example:**
\`\`\`python
user = await user_service.create_user(
    UserCreate(name="John", email="john@example.com")
)
\`\`\`
```

---

## Agent 5: Operations & Deployment Agent

**Type:** Configuration  
**Execution:** Background Cloud  
**Priority:** Medium  
**Runtime:** 5-20 minutes

### Responsibilities
- CI/CD pipeline generation (GitHub Actions)
- Deployment scripts
- Security compliance checks
- Infrastructure as Code (Terraform)
- Container configuration (Docker)
- Kubernetes manifests
- Monitoring setup

### Output Types
- `.github/workflows/*.yml` (CI/CD)
- `Dockerfile`, `docker-compose.yml`
- `k8s/*.yaml` (Kubernetes)
- `terraform/*.tf` (IaC)

### Example: GitHub Actions Workflow
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Ruff
        run: ruff check .
      - name: Run mypy
        run: mypy .
  
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest --cov
```

---

## Agent 6: Context & Knowledge Agent

**Type:** Support  
**Execution:** Background Cloud  
**Priority:** Medium  
**Runtime:** 1-5 minutes (queries), 10-30 minutes (initial population)

### Responsibilities
- Manage Context7 knowledge base
- Pre-populate library docs cache
- Cross-reference resolution
- Expert knowledge retrieval (RAG)
- Project profiling
- Cache optimization

### Context7 Management
```python
# Pre-populate common libraries
context7.populate_cache([
    "fastapi",
    "pytest",
    "pydantic",
    "sqlalchemy"
])

# Query for patterns
results = context7.query(
    query="async endpoint with database",
    library="fastapi",
    top_k=3
)
```

### Project Profiling Output
```json
{
  "deployment_type": "cloud_native",
  "tenancy": "multi_tenant",
  "user_scale": "medium",
  "compliance": ["HIPAA", "SOC2"],
  "security_posture": "high",
  "relevant_experts": [
    "healthcare",
    "security",
    "database"
  ]
}
```

---

## Foreground Agents

These run locally in Cursor IDE and require human review.

---

## Agent 7: Code Generation Agent

**Type:** Creation  
**Execution:** Foreground  
**Priority:** High  
**Runtime:** 5-20 minutes

### Responsibilities
- Implement features from specs
- Refactor code
- Fix bugs
- Add error handling
- Apply design patterns
- Generate boilerplate

### Implementation Process
```python
# 1. Read feature specification
# 2. Consult architecture design
# 3. Query Context7 for patterns
# 4. Query Expert RAG for domain patterns
# 5. Generate implementation
# 6. Add error handling & logging
# 7. Add type hints
# 8. Update tests
# 9. Document changes
```

### Output Format
```json
{
  "changes": [
    {
      "file": "src/api/users.py",
      "type": "feature",
      "lines_added": 87,
      "lines_removed": 12,
      "functions_added": ["authenticate_user"]
    }
  ],
  "refactorings": [
    {
      "file": "src/utils.py",
      "type": "refactor",
      "before_complexity": 12,
      "after_complexity": 4
    }
  ]
}
```

---

## Agent 8: Design & Architecture Agent

**Type:** Planning  
**Execution:** Foreground  
**Priority:** High  
**Runtime:** 10-30 minutes

### Responsibilities
- System architecture planning
- Design pattern recommendations
- Database schema design
- API design
- Expert consultation (16 builtin + N industry)
- Technology recommendations

### Expert Consultation Flow
```python
async def design_payment_system(requirements):
    # 1. Identify relevant experts
    experts = [
        "healthcare (industry, 51%)",
        "fintech (industry, 24.5%)",
        "security (builtin, 12.25%)",
        "performance (builtin, 12.25%)"
    ]
    
    # 2. Query each expert
    recommendations = []
    for expert in experts:
        rec = await expert.consult(requirements)
        recommendations.append((expert, rec, expert.weight))
    
    # 3. Weighted decision
    return weighted_combine(recommendations)
```

### Output Format
```json
{
  "architecture_style": "Microservices",
  "components": [
    {
      "name": "Payment Gateway",
      "technology": "FastAPI",
      "expert_recommendations": {
        "healthcare": "HIPAA compliance required",
        "fintech": "PCI DSS Level 1",
        "security": "Tokenize card data"
      }
    }
  ],
  "database_schema": {...},
  "api_design": {...}
}
```

---

## Agent 9: Review & Improvement Agent

**Type:** Analysis  
**Execution:** Foreground  
**Priority:** High  
**Runtime:** 3-15 minutes

### Responsibilities
- Code review with 5-metric scoring
- Security review
- Performance review
- Best practices enforcement
- Refactoring recommendations
- PR comments

### Scoring System
```python
weighted_score = (
    complexity_score * 0.20 +
    security_score * 0.25 +
    maintainability_score * 0.20 +
    test_coverage_score * 0.20 +
    performance_score * 0.15
)

# Decision thresholds:
# >= 8.0: APPROVED
# >= 6.0: APPROVED_WITH_SUGGESTIONS
# < 6.0: CHANGES_REQUESTED
```

### Output Format
```json
{
  "overall_score": 8.7,
  "decision": "APPROVED",
  "comments": [
    {
      "file": "api/users.py",
      "line": 42,
      "severity": "suggestion",
      "message": "Consider using async/await"
    }
  ],
  "security_findings": [],
  "refactoring_suggestions": [...]
}
```

---

## Agent 10: Planning & Analysis Agent

**Type:** Planning  
**Execution:** Foreground  
**Priority:** High  
**Runtime:** 10-30 minutes

### Responsibilities
- User story generation
- Epic breakdown
- Effort estimation
- Risk analysis
- Requirement validation
- Sprint planning

### Output Format
```markdown
# Epic: User Authentication

## User Story 1: User Registration
**As a** new user  
**I want to** create an account  
**So that** I can access the application

**Acceptance Criteria:**
- Email must be unique
- Password complexity requirements
- Email confirmation required

**Effort:** 5 story points (8 hours)  
**Risk:** Low  
**Dependencies:** Email service
```

---

## Agent 11: Enhancement & Prompt Agent

**Type:** Optimization  
**Execution:** Foreground  
**Priority:** Medium  
**Runtime:** 2-8 minutes

### Responsibilities
- Transform simple → comprehensive prompts
- 7-stage enhancement pipeline
- Domain detection
- Expert integration
- Context analysis

### Enhancement Pipeline
```python
# Stage 1: Context analysis
# Stage 2: Domain detection
# Stage 3: Expert consultation
# Stage 4: Requirement elaboration
# Stage 5: Constraint identification
# Stage 6: Example generation
# Stage 7: Validation criteria
```

### Example Enhancement

**Input:** "Build a payment system"

**Output:**
```markdown
# Enhanced Prompt: Payment Processing System

## Context
Healthcare application requiring HIPAA-compliant payment processing.

## Requirements
1. Payment methods: Credit card, ACH, HSA/FSA
2. Compliance: PCI DSS Level 1, HIPAA
3. Security: Tokenization, encryption

## Expert Recommendations
- Healthcare: 7-year retention (HIPAA)
- Fintech: Use tokenization
- Security: 3D Secure 2.0

## Validation Criteria
- [ ] Payment data encrypted
- [ ] No CVV in logs
- [ ] 7-year retention
```

---

## Agent Summary Table

| Agent | Type | Execution | Priority | Runtime | Resource |
|-------|------|-----------|----------|---------|----------|
| **Orchestration** | Coordination | Foreground | Critical | Continuous | Low |
| **Quality** | Analysis | Background | Medium | 2-10 min | Medium CPU |
| **Testing** | Execution | Background | High | 5-30 min | Medium |
| **Docs** | Creation | Background | Low | 3-15 min | Low |
| **Ops** | Configuration | Background | Medium | 5-20 min | Medium |
| **Context** | Support | Background | Medium | 1-5 min | Medium |
| **Code** | Creation | Foreground | High | 5-20 min | Medium |
| **Design** | Planning | Foreground | High | 10-30 min | Medium |
| **Review** | Analysis | Foreground | High | 3-15 min | Low |
| **Planning** | Planning | Foreground | High | 10-30 min | Low |
| **Enhancement** | Optimization | Foreground | Medium | 2-8 min | Low |

---

**Next Document:** Part 3 - Communication Architecture
