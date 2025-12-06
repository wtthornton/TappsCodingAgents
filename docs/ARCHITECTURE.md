# Architecture Overview

**Version**: 1.5.0  
**Last Updated**: December 2025

## System Architecture

TappsCodingAgents is built on a two-layer agent model with a modular, extensible architecture designed for scalability and flexibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TappsCodingAgents Framework                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐         ┌──────────────────────┐    │
│  │  Workflow Agents     │         │  Industry Experts    │    │
│  │  (Execution Layer)   │◄───────►│  (Knowledge Layer)   │    │
│  │                      │         │                      │    │
│  │  • Analyst           │         │  • Domain-Specific   │    │
│  │  • Planner           │         │  • Weighted Decision │    │
│  │  • Architect         │         │  • RAG-Enhanced      │    │
│  │  • Designer          │         │  • Config-Based      │    │
│  │  • Implementer       │         │                      │    │
│  │  • Tester            │         └──────────────────────┘    │
│  │  • Debugger          │                  │                  │
│  │  • Documenter        │                  │                  │
│  │  • Reviewer          │                  │                  │
│  │  • Improver          │                  ▼                  │
│  │  • Ops               │         ┌──────────────────────┐    │
│  │  • Orchestrator      │         │  Knowledge Base      │    │
│  └──────────────────────┘         │  (File-Based RAG)    │    │
│           │                        │                      │    │
│           ▼                        │  • Markdown Files    │    │
│  ┌──────────────────────┐         │  • Domain Knowledge  │    │
│  │  Model Abstraction   │         │  • Best Practices    │    │
│  │  Layer (MAL)         │         └──────────────────────┘    │
│  │                      │                  │                  │
│  │  • Local (Ollama)    │                  │                  │
│  │  • Cloud Fallback    │                  ▼                  │
│  │    - Anthropic       │         ┌──────────────────────┐    │
│  │    - OpenAI          │         │  Context7 Integration│    │
│  └──────────────────────┘         │  (Library Docs KB)   │    │
│           │                        │                      │    │
│           ▼                        │  • KB-First Cache    │    │
│  ┌──────────────────────┐         │  • Auto-Refresh      │    │
│  │  MCP Gateway         │         │  • Cross-References  │    │
│  │                      │         └──────────────────────┘    │
│  │  • Filesystem Tools  │                  │                  │
│  │  • Git Tools         │                  │                  │
│  │  • Analysis Tools    │                  ▼                  │
│  └──────────────────────┘         ┌──────────────────────┐    │
│                                    │  Quality Analysis    │    │
│                                    │                      │    │
│                                    │  • Code Scoring      │    │
│                                    │  • Ruff Linting      │    │
│                                    │  • mypy Type Check   │    │
│                                    │  • TS/JS Support     │    │
│                                    │  • Dependency Audit  │    │
│                                    └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Workflow Agents (Execution Layer)

12 specialized agents that execute SDLC tasks:

- **Planning**: Analyst, Planner
- **Design**: Architect, Designer
- **Development**: Implementer, Debugger, Documenter
- **Testing**: Tester
- **Quality**: Reviewer, Improver
- **Operations**: Ops
- **Orchestration**: Orchestrator

**Key Features:**
- Star-prefixed command system (`*review`, `*plan`, etc.)
- Activation instructions for AI assistants
- Path validation and error handling
- Consistent interface via `BaseAgent`

### 2. Industry Experts (Knowledge Layer)

Domain-specific business authorities that provide context and decision-making guidance.

**Key Features:**
- Configuration-only (YAML-based, no code required)
- Weighted decision-making (51% primary authority)
- File-based RAG for knowledge retrieval
- Consult-based integration with workflow agents

**Architecture Pattern:**
```
Expert Configuration (YAML)
    ↓
Expert Registry (Weighted Selection)
    ↓
Knowledge Base (RAG Retrieval)
    ↓
Workflow Agent Consultation
```

### 3. Model Abstraction Layer (MAL)

Unified interface for local and cloud LLM providers.

**Provider Priority:**
1. **Local** (Ollama) - Fast, free, offline
2. **Cloud Fallback** (Anthropic Claude) - High quality
3. **Cloud Fallback** (OpenAI GPT) - Alternative option

**Benefits:**
- Seamless provider switching
- Cost optimization (local-first)
- Reliability (automatic fallback)
- Consistent API across providers

### 4. MCP Gateway

Unified access to Model Context Protocol tools.

**Supported Tools:**
- **Filesystem**: Read/write operations
- **Git**: Version control operations
- **Analysis**: Code analysis and parsing

**Architecture:**
```
Workflow Agent
    ↓
MCP Gateway (Unified Interface)
    ↓
MCP Server (Tool-Specific)
    ↓
External Tool (Filesystem/Git/Analysis)
```

### 5. Quality Analysis System

Comprehensive code quality metrics and analysis.

**Phase 6 Enhancements (2025 Standards):**
- **Ruff**: Python linting (10-100x faster)
- **mypy**: Static type checking
- **ESLint/TypeScript**: Frontend code analysis
- **jscpd**: Code duplication detection
- **pip-audit**: Dependency security scanning
- **Multi-format reporting**: JSON, Markdown, HTML

**Scoring Metrics:**
1. Complexity (Cyclomatic complexity)
2. Security (Vulnerability detection)
3. Maintainability (Maintainability Index)
4. Test Coverage (Coverage analysis)
5. Performance (Static analysis)

### 6. Context7 Integration

Intelligent library documentation caching and retrieval.

**Features:**
- KB-first lookup (cache before API)
- Auto-refresh for stale entries
- Cross-reference detection
- Performance analytics
- Cleanup automation

**Workflow:**
```
Agent Request → KB Cache Check → [Hit] Return Cached
                                  [Miss] → Context7 API → Cache → Return
```

### 7. Tiered Context System

Intelligent context injection with 90%+ token savings.

**Three Tiers:**
1. **Tier 1**: Essential context (always included)
2. **Tier 2**: Relevant context (conditionally included)
3. **Tier 3**: Extended context (rarely included)

**Caching:**
- In-memory cache for frequently accessed context
- Automatic cache invalidation
- Configurable cache size limits

## Data Flow

### Agent Execution Flow

```
User Command/Query
    ↓
Orchestrator Agent (if workflow)
    ↓
Target Workflow Agent
    ↓
1. Load Configuration
2. Activate Agent (validate paths, setup)
3. Execute Command (*command)
4. Consult Experts (if needed)
5. Use MAL for LLM calls
6. Use MCP Gateway for tools
7. Return Results
```

### Expert Consultation Flow

```
Workflow Agent Needs Domain Knowledge
    ↓
Query Expert Registry
    ↓
Select Primary Expert (51% weight)
    ↓
Query Knowledge Base (RAG)
    ↓
Retrieve Relevant Context
    ↓
Return Weighted Decision/Advice
```

### Quality Analysis Flow

```
Reviewer Agent Activated
    ↓
Scan Target Files
    ↓
Run Quality Tools (Ruff, mypy, etc.)
    ↓
Calculate Scores (5 metrics)
    ↓
Generate Reports (JSON/Markdown/HTML)
    ↓
Aggregate (Service/Project Level)
```

## Configuration System

### Configuration Hierarchy

```
Default Config (templates/default_config.yaml)
    ↓
Project Config (project_config.yaml)
    ↓
User Config (user_config.yaml)
    ↓
Runtime Overrides (Environment Variables)
```

### Key Configuration Files

- **`project_config.yaml`**: Project-specific settings
- **`experts.yaml`**: Expert definitions
- **`domains.md`**: Domain descriptions
- **`workflows/*.yaml`**: Workflow definitions

## Extension Points

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement required methods (`activate`, `get_commands`, `run`)
3. Add configuration in `config.py`
4. Register in agent registry

### Adding New Experts

1. Create YAML configuration in `experts/` directory
2. Add knowledge base files in `knowledge/` directory
3. Update `domains.md` with domain description
4. Expert registry auto-discovers new experts

### Adding New Quality Tools

1. Add tool configuration to `QualityToolsConfig`
2. Implement scoring logic in `CodeScorer` or specialized scorer
3. Add commands to `ReviewerAgent`
4. Update report generator templates

## Performance Considerations

### Caching Strategy
- **Context**: Tiered context system with LRU cache
- **Context7**: KB cache with staleness policies
- **RAG**: Knowledge base chunking and indexing
- **Quality**: Report caching for historical tracking

### Optimization Techniques
- Lazy loading of heavy dependencies
- Parallel processing for multi-service analysis
- Incremental quality analysis
- Async/await for I/O operations

## Security Architecture

### Access Control
- Read-only vs write permissions per agent
- Path validation before file operations
- Sandboxed execution for external tools
- Configuration file validation

### Data Privacy
- Local-first model usage
- Optional cloud fallback (user-controlled)
- No telemetry or data collection
- Secure credential management

## Deployment Architecture

### Local Development
- Python virtual environment
- Ollama for local LLM
- File-based storage
- Direct CLI access

### Production Deployment
- Containerized (Docker)
- Cloud LLM providers (Anthropic/OpenAI)
- Persistent storage for KB cache
- CI/CD integration ready

## Future Enhancements

### Planned Architecture Improvements
- Vector DB integration for RAG (if needed)
- Workflow state persistence
- Advanced analytics dashboard
- Distributed agent execution

---

**Related Documentation:**
- [Configuration Guide](CONFIGURATION.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [API Documentation](API.md)
- [Project Requirements](../requirements/PROJECT_REQUIREMENTS.md)

