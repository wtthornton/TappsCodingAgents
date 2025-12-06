# Changelog

All notable changes to TappsCodingAgents will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2025-12-XX

### Added
- **Enhancer Agent - Prompt Enhancement Utility**
  - Full 7-stage enhancement pipeline (analysis, requirements, architecture, codebase context, quality, implementation, synthesis)
  - Quick enhancement mode (stages 1-3) for fast iteration
  - Stage-by-stage execution for debugging and customization
  - Session management with save/resume capability
  - Industry Expert integration with weighted consultation
  - Multiple output formats (Markdown, JSON, YAML)
  - CLI commands: `enhance`, `enhance-quick`, `enhance-stage`, `enhance-resume`
  - Configuration system via `.tapps-agents/enhancement-config.yaml`
  - Workflow definition: `workflows/prompt-enhancement.yaml`
  - Comprehensive documentation and examples
  - See [Enhancer Agent Guide](docs/ENHANCER_AGENT.md) for details

## [1.5.0] - 2025-12-XX

### Added
- **Phase 6.4.4: TypeScript & JavaScript Support**
  - TypeScript scorer module with ESLint and TypeScript compiler integration
  - Support for `.ts`, `.tsx`, `.js`, `.jsx` file types
  - Automatic file type routing in Reviewer Agent
  - Enhanced `lint_file()` and `type_check_file()` methods for multi-language support

- **Phase 6.4.3: Dependency Security Auditing**
  - Dependency analyzer module with pip-audit and pipdeptree integration
  - Ops Agent commands: `*audit-dependencies`, `*dependency-tree`, `*check-vulnerabilities`
  - Dependency health integration into Reviewer Agent security scoring
  - Configurable severity thresholds for vulnerability reporting

- **Phase 6.4.2: Multi-Service Analysis**
  - Service discovery module for auto-detecting services
  - Quality aggregator for service-level and project-level aggregation
  - Parallel analysis with asyncio for batch processing
  - Cross-service quality comparison
  - `*analyze-project` and `*analyze-services` commands

- **Phase 6.4.1: Code Duplication Detection**
  - jscpd integration for Python and TypeScript
  - Duplication score calculation in CodeScorer
  - `*duplication` command in Reviewer Agent
  - Configurable duplication thresholds

### Changed
- Updated Reviewer Agent to support multi-language quality analysis
- Enhanced quality scoring to include dependency health metrics
- Improved report generation with service-level aggregation

### Documentation
- Created comprehensive documentation structure following 2025 best practices
- Added API reference documentation
- Created contributing guidelines
- Added architecture documentation

## [1.4.0] - 2025-12-XX

### Added
- **Phase 6.3: Comprehensive Reporting Infrastructure**
  - Report generator module with JSON, Markdown, and HTML formats
  - Historical tracking for quality trends
  - Interactive HTML dashboards with Plotly integration
  - Jinja2 template support for custom report formats
  - `*report` command enhancement

- **Phase 6.2: mypy Type Checking Integration**
  - mypy integration for static type checking
  - Type checking score calculation
  - `*type-check` command in Reviewer Agent
  - Support for mypy.ini and pyproject.toml configuration

- **Phase 6.1: Ruff Integration**
  - Ruff linting integration (10-100x faster than pylint)
  - Linting score calculation
  - `*lint` command in Reviewer Agent
  - Support for ruff.toml and pyproject.toml configuration

## [1.3.0] - 2025-12-XX

### Added
- **Phase 5: Context7 Integration (Complete)**
  - KB-first caching system for library documentation
  - Auto-refresh queue for stale cache entries
  - Cross-reference detection and navigation
  - Performance analytics and monitoring
  - KB cleanup automation
  - Agent integration helper for Context7 commands
  - Comprehensive CLI commands for KB management
  - Integrated into Architect, Implementer, and Tester agents

### Changed
- Improved documentation caching with intelligent staleness policies
- Enhanced fuzzy matching for library name resolution

## [1.2.0] - 2025-12-XX

### Added
- **Phase 4: Scale-Adaptive Workflow Selection**
  - Project type auto-detection (Greenfield, Brownfield, Quick-Fix, Hybrid)
  - Workflow recommendation system with confidence scoring
  - Automatic workflow selection integration

- **Phase 3: Example Expert Implementations**
  - 4 example expert configurations (home-automation, healthcare, financial-services, ecommerce)
  - Expert templates and knowledge base examples
  - Best practices documentation

### Changed
- Enhanced workflow executor with automatic workflow selection

## [1.1.0] - 2025-12-XX

### Added
- **Enhanced Features**
  - Code Scoring System with 5 metrics (complexity, security, maintainability, test_coverage, performance)
  - Tiered Context Injection (90%+ token savings)
  - MCP Gateway (Unified Model Context Protocol interface)
  - YAML Workflow Definitions (Declarative orchestration)
  - Greenfield/Brownfield Workflow support

- **Industry Experts Framework**
  - Configuration-only expert definition
  - Weighted decision-making (51% primary authority)
  - File-based RAG for knowledge retrieval
  - Expert registry and consultation system

## [1.0.0] - 2025-12-XX

### Added
- **Core Framework**
  - 12 Workflow Agents (analyst, planner, architect, designer, implementer, tester, debugger, documenter, reviewer, improver, ops, orchestrator)
  - BaseAgent class with BMAD-METHOD patterns
  - Star-prefixed command system
  - Configuration system (YAML-based, Pydantic validated)
  - Model Abstraction Layer (MAL) with Ollama + Cloud Fallback
  - Path validation and error handling
  - Activation instructions for AI assistants

- **Testing**
  - Comprehensive test suite (500+ tests)
  - Unit and integration tests
  - Test coverage reporting

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|--------------|
| 1.6.0 | Dec 2025 | Enhancer Agent - Prompt Enhancement Utility with Expert Integration |
| 1.5.0 | Dec 2025 | Phase 6 Complete - Modern Quality Analysis (Ruff, mypy, TypeScript, multi-service, dependencies) |
| 1.4.0 | Dec 2025 | Phase 6.1-6.3 - Reporting, Type Checking, Ruff Integration |
| 1.3.0 | Dec 2025 | Phase 5 Complete - Context7 Integration |
| 1.2.0 | Dec 2025 | Phase 3-4 - Examples and Workflow Selection |
| 1.1.0 | Dec 2025 | Enhanced Features and Industry Experts |
| 1.0.0 | Dec 2025 | Core Framework |

---

## Upcoming Features

- Enhanced test coverage for Phase 6 components
- TypeScript support integration in Implementer and Tester agents
- Advanced analytics dashboard
- Workflow state persistence
- Vector DB integration for RAG (if needed)

---

**Note**: This changelog is maintained according to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) principles.

