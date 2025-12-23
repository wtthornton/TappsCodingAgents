# Release v2.6.0 - Epic Workflows, Coverage-Driven Testing, Docker Debugging, and Microservice Generation

**Release Date:** January 28, 2026  
**Tag:** v2.6.0

## 🎉 Major New Features

### Epic Workflow Orchestration

Execute Epic documents with automatic story dependency resolution and quality gate enforcement.

**Key Features:**
- Epic document parsing with story extraction and dependency resolution
- Topological sort (Kahn's algorithm) for story execution order
- Quality gate enforcement after each story with automatic loopback
- Progress tracking and completion reports
- Simple Mode command: `@simple-mode *epic <epic-doc.md>`

**Usage:**
```
@simple-mode *epic docs/prd/epic-51-yaml-automation-quality-enhancement.md
```

**Documentation:** [Epic Workflow Guide](docs/EPIC_WORKFLOW_GUIDE.md)

### Coverage-Driven Test Generation

Intelligent test generation based on coverage gaps.

**Key Features:**
- Coverage analyzer for JSON and .coverage database formats
- Gap identification and prioritization
- Targeted test generation for uncovered code paths
- Integration with test generators for automatic gap filling
- Coverage threshold checking and reporting

**Usage:**
```bash
python -m tapps_agents.cli tester analyze-coverage coverage.json --target 80
python -m tapps_agents.cli tester generate-coverage-tests coverage.json --module src/clients
```

### Docker Debugging Capabilities

Automated Docker container issue diagnosis with pattern matching and fix suggestions.

**Key Features:**
- Dockerfile analysis for common issues (Python path, WORKDIR, COPY order)
- Container log retrieval and analysis
- Error pattern matching with confidence scoring
- Automatic fix suggestions based on known patterns
- Pattern learning from successful fixes

**Usage:**
```bash
python -m tapps_agents.cli ops docker-debug "ModuleNotFoundError" --service my-service
python -m tapps_agents.cli ops docker-analyze Dockerfile
```

### Microservice Generation

Automated microservice boilerplate generation with Docker support.

**Key Features:**
- FastAPI and Flask service templates
- Dockerfile and docker-compose integration
- Health check endpoints
- Test scaffolding
- HomeIQ-specific patterns support

**Usage:**
```bash
python -m tapps_agents.cli templates microservice "my-service" --port 8000 --type fastapi
```

### Service Integration Automation

Automate service-to-service integration with client generation and configuration updates.

**Key Features:**
- Client class generation
- Configuration file updates
- Dependency injection setup
- Integration test generation

### Quality Gate Enforcement

Mandatory quality checks with automatic loopback on failures.

**Key Features:**
- Configurable quality thresholds (overall, security, maintainability, test coverage)
- Critical service detection with higher thresholds
- Automatic improvement loopback on quality failures
- Integration with Epic workflows for story-level enforcement

## 🔧 Additional Features

### Test Fixing Capabilities
- Pattern-based test failure detection
- Common issue fixes (async/await, authentication, mocks)
- Batch test fixing support
- Test modernization (e.g., TestClient → AsyncClient migration)

### Batch Test Generation
- Generate tests for multiple files simultaneously
- Shared fixture detection
- Consistent test patterns across files
- Integration test support

### Context-Aware Test Generation
- Learn from existing test patterns
- Test style matching
- Fixture reuse
- Pattern recognition from codebase

### Service Integration Testing
- Generate service-to-service integration tests
- Internal authentication handling
- Dependency mocking
- Service-to-service communication patterns

## 📚 Documentation Updates

- ✅ New Epic Workflow Guide (`docs/EPIC_WORKFLOW_GUIDE.md`)
- ✅ Updated Simple Mode Guide with Epic intent
- ✅ Updated Agent Capabilities with new features
- ✅ Updated Command Reference
- ✅ Updated README with Epic examples

## 🐛 Bug Fixes

- Fixed syntax errors in reviewer agent exception handlers
- Fixed unused imports and variables in Epic orchestrator
- All linting issues resolved (ruff check passes)

## 📦 Installation

```bash
pip install tapps-agents==2.6.0
```

## 🔗 Links

- [Epic Workflow Guide](docs/EPIC_WORKFLOW_GUIDE.md)
- [Simple Mode Guide](docs/SIMPLE_MODE_GUIDE.md)
- [Command Reference](docs/TAPPS_AGENTS_COMMAND_REFERENCE.md)
- [Full Changelog](CHANGELOG.md)

## 📊 Statistics

- **New Components:** 15+ new modules
- **New Commands:** 10+ new commands
- **Documentation:** 3 new guides, 5 updated guides
- **Code Quality:** All linting issues resolved

## 🎯 What's Next

- Enhanced Epic workflow features
- Additional Docker debugging patterns
- More microservice templates
- Enhanced service integration capabilities

---

**Full Changelog:** [CHANGELOG.md](CHANGELOG.md#260---2026-01-28)

