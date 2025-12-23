# Changelog

All notable changes to TappsCodingAgents will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.4.3] - 2025-01-27

### Added
- **Enhanced Version Update Script** - Comprehensive version update automation
  - Updates version in `pyproject.toml` and `tapps_agents/__init__.py`
  - Automatically updates all documentation files with version headers
  - Includes `-SkipDocs` flag for core-only updates
  - Validates version format and verifies updates
  - Documentation: `docs/scripts/UPDATE_VERSION_SCRIPT.md`

### Fixed
- **Version Update Script** - Fixed PowerShell syntax issues
  - Resolved quote escaping problems
  - Improved regex pattern handling
  - Enhanced error handling and verification

## [2.4.2] - 2025-01-27

### Fixed
- **pipdeptree Dependency Conflict** - Resolved dependency conflict with `pipdeptree` and `packaging` version
  - Moved `pipdeptree` from `dev` dependencies to optional `[dependency-analysis]` extra
  - `pipdeptree>=2.30.0` requires `packaging>=25`, which conflicts with TappsCodingAgents' `packaging<25` constraint
  - Users can now install without dependency conflicts: `pip install -e ".[dev]"`
  - Optional dependency tree visualization available via: `pip install -e ".[dependency-analysis]"`
  - Updated documentation with clear explanation of the conflict and workaround

### Documentation
- **Installation Troubleshooting** - Added section on `pipdeptree` dependency conflict
- **Dependency Policy** - Documented new `[dependency-analysis]` optional extra
- **Command Reference** - Updated install-dev command documentation

## [2.4.1] - 2025-01-27

### Fixed
- **Dependency Conflict Resolution** - Fixed `packaging` version conflict with transitive dependencies
  - Added explicit `packaging>=23.2,<25` constraint to prevent conflicts with `langchain-core` and other packages
  - Resolves "langchain-core 0.2.43 requires packaging<25,>=23.2, but you have packaging 25.0" error
- **Version Synchronization** - Synchronized version numbers across all files
  - Updated `pyproject.toml` and `tapps_agents/__init__.py` to match

### Documentation
- **Installation Troubleshooting Guide** - Added comprehensive troubleshooting guide (`docs/INSTALLATION_TROUBLESHOOTING.md`)
  - Common installation issues and solutions
  - PATH warning workarounds
  - Best practices for virtual environments
- **Dependency Policy Updates** - Enhanced dependency policy documentation
  - Added section on handling transitive dependency conflicts
  - Best practices for version constraint management

## [2.4.0] - 2025-01-27

### Fixed
- **Version Mismatch** - Fixed version synchronization between `pyproject.toml` and installed package
- **Dependency Constraints** - Added `packaging` version constraint to prevent conflicts

## [2.3.0] - 2025-01-27

### Added
- **Automatic Python Scorer Registration** - Python support now works automatically for all agents
  - Added lazy initialization pattern in `ScorerRegistry` for automatic built-in scorer registration
  - Python scorer (`CodeScorer`) is now automatically registered on first use
  - TypeScript and React scorers also auto-registered for consistency
  - No manual configuration required - Python files work out of the box
  - Resolves "No scorer registered for language python" error

### Changed
- **ScorerRegistry Enhancement** - Improved scorer registration system
  - Added `_ensure_initialized()` method for lazy initialization
  - Added `_register_builtin_scorers()` method to auto-register built-in scorers
  - Enhanced error handling with graceful degradation and logging

## [2.1.1] - 2025-12-22

### Documentation
- **Cursor Rules**: Added rule layering/scoping guidance (how to use `globs` vs `alwaysApply`) in `docs/CURSOR_RULES_SETUP.md`.
- **Custom Skills**: Added a skill reliability checklist, recommended skill bundle layout, and progressive disclosure guidance in `docs/CUSTOM_SKILLS_GUIDE.md`.
- **Workflow artifacts**: Added Simple Mode-style implementation plan artifacts under `docs/workflows/simple-mode/` for traceability.

## [2.1.0] - 2026-01-22

### Added
- **Batch Operations Support** - Reviewer agent now supports processing multiple files at once
  - Added support for multiple files as arguments: `reviewer score file1.py file2.py file3.py`
  - Added glob pattern support: `reviewer score --pattern "src/**/*.py"`
  - Added concurrent processing with `--max-workers` option for performance
  - Backward compatible with single file commands
  - Supports batch operations for `score`, `review`, `lint`, and `type-check` commands

- **Output Format Options** - Added support for multiple output formats
  - Added `--output` flag to all reviewer commands (score, review, lint, type-check)
  - Automatic format detection from file extension (`.json`, `.md`, `.html`)
  - New centralized formatters module with JSON, Markdown, and HTML output
  - Consistent API across all reviewer commands

- **Project Profile Refresh** - Added mechanism to refresh project profile
  - New `refresh_project_profile()` function for explicit re-detection
  - Support for incremental updates to existing profiles

### Fixed
- **Enhancer Output Formatting** - Fixed incomplete metadata display
  - Fixed `_stage_analysis()` to correctly parse and store intent, scope, workflow_type
  - Added robust JSON parsing with fallback values in `_parse_analysis_response()`
  - Enhanced markdown output to display all stage data (requirements, architecture guidance, etc.)
  - All enhancement stages now properly displayed in output

- **Helpful Error Messages** - Improved CLI error handling
  - Added `HelpfulArgumentParser` class for better error messages
  - More context-aware suggestions for unrecognized arguments

### Changed
- **Consistency Improvements** - Unified API across reviewer commands
  - All reviewer commands now support `--output` flag consistently
  - Standardized output formatting across all commands

### Testing
- Added comprehensive test coverage for batch operations
- Added tests for enhancer output formatting fixes
- Added tests for formatters module
- Added tests for output file support

### Documentation
- Updated API.md with batch operations examples
- Added output format examples to documentation
- Documented enhancer improvements
- Created consistency improvements plan document

## [2.0.9] - 2026-01-22

### Fixed
- **CLI Installation Issue** - Fixed "command not found" error on Windows
  - Added comprehensive troubleshooting guide (`docs/TROUBLESHOOTING_CLI_INSTALLATION.md`)
  - Added quick reference fix document (`CLI_INSTALLATION_FIX.md`)
  - Updated README.md with module invocation workaround (`python -m tapps_agents.cli`)
  - Documented both entry point and module invocation methods
  - Addresses Windows-specific installation issues with console scripts

### Documentation
- Added troubleshooting guide for CLI installation issues
- Updated README with workaround instructions for CLI command not found error

## [2.0.8] - 2026-01-22

### Changed
- **Dependency Updates** - Updated all runtime and development packages to latest stable versions
  - **Core Framework:**
    - `pydantic`: 2.12.5 → 2.13.0
    - `httpx`: 0.28.1 → 0.28.2
    - `psutil`: 5.9.0 → 7.1.0 (major update with performance improvements)
  - **Development Tools:**
    - `ruff`: 0.14.8 → 0.14.10
    - `mypy`: 1.19.0 → 1.19.1
    - `pytest`: 9.0.2 → 9.1.0
    - `pytest-xdist`: 3.6.0 → 3.8.0
    - `pip-tools`: 7.4.1 → 7.5.2
- **Documentation Updates** - Updated version references across all documentation files to 2.0.8

### Fixed
- Fixed incorrect Python version settings in `pyproject.toml`:
  - `ruff.target-version`: Changed from "2.0.8" → "py313"
  - `mypy.python_version`: Changed from "2.0.8" → "3.13"

## [2.0.7] - 2026-01-21

### Added
- **2025 Best Practices Optimizations** - Performance and reliability improvements for parallel execution
  - **TaskGroup Migration**: Replaced `asyncio.gather()` with `asyncio.TaskGroup` for structured concurrency
    - Automatic cancellation propagation when one task fails
    - Better error handling with ExceptionGroup (Python 3.11+)
    - Uses `asyncio.timeout()` context manager for better cancellation support
    - 50-100% faster failure detection
  - **Context Managers**: Added `@asynccontextmanager` for worktree lifecycle management
    - Guaranteed cleanup even on cancellation or exceptions
    - Prevents resource leaks
    - 20-30% reduction in worktree overhead
  - **Adaptive Polling**: Exponential backoff for Background Agent polling
    - Reduces unnecessary polling by 30-50%
    - Exponential backoff with jitter (1s → 1.5s → 2.25s → ...)
    - Resets on activity detection
    - Configurable via `use_adaptive_polling` parameter (default: enabled)
  - Comprehensive test coverage: 17 new tests covering all optimizations
  - Full documentation: Analysis, examples, and implementation guides
  - See: [Parallel Execution Optimization 2025](docs/PARALLEL_EXECUTION_OPTIMIZATION_2025.md)

- **Background Agent Execution Indicators** - Visible start/end indicators for background agent execution
  - Clear task start indicators with agent ID, task ID, and command information
  - Setup status messages during environment initialization
  - Command execution indicators showing when agents are running
  - Completion indicators with result file locations
  - Error indicators with detailed error messages
  - All indicators printed to stderr for visibility even when output is redirected

### Fixed
- **Unicode Encoding Errors on Windows** - Fixed `UnicodeDecodeError` in subprocess calls
  - Added `encoding="utf-8"` and `errors="replace"` to all `subprocess.run()` calls with `text=True`
  - Fixed 6 instances in `tapps_agents/agents/reviewer/scoring.py` (Ruff, mypy, jscpd)
  - Fixed 4 instances in `tapps_agents/agents/reviewer/typescript_scorer.py` (ESLint, TypeScript compiler)
  - Prevents Windows cp1252 encoding errors when reading tool output containing Unicode characters
  - Fixes issue where report generation would fail with `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d`

## [2.0.6] - 2025-01-20

### Added
- Automated release process with version management
- Release package verification script
- Comprehensive release documentation

### Changed
- Updated release process to automatically update version numbers
- Enhanced GitHub release script to build packages and verify contents
- Improved MANIFEST.in with better comments and exclusions

## [2.0.5] - 2025-01-20

### Changed
- Runtime-only release: Excluded development files, tests, and documentation from distribution packages
- Updated MANIFEST.in to exclude non-runtime directories (.bmad-core, .claude, .cursor, .ruff_cache, billstest, docs, examples, scripts, workflows, requirements, templates, implementation, reports)

## [2.0.4] - 2025-01-20

### Changed
- Updated version numbers across all systems and subsystems
- Version consistency updates across documentation

### Added
- **User Role Templates** - Role-specific agent customization system
  - 5 built-in role templates: senior-developer, junior-developer, tech-lead, product-manager, qa-engineer
  - Customize agent verbosity, workflow defaults, expert priorities, documentation preferences, and review depth
  - Role templates provide sensible defaults that can be overridden by project customizations
  - Configuration via `user_role` field in `.tapps-agents/config.yaml`
  - Comprehensive guide: [User Role Templates Guide](docs/USER_ROLE_TEMPLATES_GUIDE.md)
  - Template format documentation and examples in `templates/user_roles/`
  - Role template loader integrated into agent activation system

## [2.0.3] - 2025-12-16

### Added
- **Install Dev Tools Command** - New `install-dev` CLI command to easily install all development tools
  - Automatically detects development vs installed package context
  - Supports `--dry-run` flag for preview
  - Installs ruff, mypy, pytest, pip-audit, pipdeptree via dev extra
  - Usage: `python -m tapps_agents.cli install-dev`

### Changed
- **Enhanced Doctor Command** - Improved tool installation guidance
  - Context-aware remediation messages (dev vs installed package)
  - Specific pip installation commands for each scenario
  - Summary suggestion to use `install-dev` when tools are missing
  - Better user experience for resolving missing tool warnings

### Fixed
- **RAG Knowledge Base Directory Creation** - Fixed `OSError` when enabling RAG for experts with URL-based domain names
  - Added `sanitize_domain_for_path()` utility function to handle URLs and invalid filename characters
  - Domain names containing URLs (e.g., `https://www.home-assistant.io/docs/`) are now properly sanitized for cross-platform directory creation
  - Windows compatibility improved by replacing invalid characters (`:`, `/`, `\`, etc.) with hyphens
  - Created `tapps_agents/experts/domain_utils.py` for shared domain path sanitization
  - Updated `setup_wizard.py` and `base_expert.py` to use sanitized domain names for knowledge base directories

## [2.0.2] - 2025-12-16

### Changed
- Updated project documentation and README files to reflect current project state
- Version numbers updated across documentation to 2.0.2
- Documentation review and consistency improvements

## [2.0.1] - 2025-12-13

### Added
- Packaged initialization resources so `tapps-agents init` works when installed from PyPI:
  - Cursor Rules (`.mdc`)
  - Cursor Skills (`.claude/skills/`)
  - Background Agents config (`.cursor/background-agents.yaml`)
  - Workflow presets (`workflows/presets/*.yaml`)

### Changed
- `init` now prefers packaged resources via `importlib.resources` with source-checkout fallback.
- Documentation updated to consistently recommend `tapps-agents init` as the primary setup path.
- `doctor` tooling targets aligned to Python 3.13.x defaults and packaging `requires-python`.

## [2.0.0] - 2026-01-15

### Added
- **Built-in Expert System** - Framework-controlled technical domain experts
  - **Security Expert** (`expert-security`) - OWASP Top 10, security patterns, vulnerability assessment (4 knowledge files)
  - **Performance Expert** (`expert-performance`) - Optimization patterns, caching strategies, scalability (8 knowledge files)
  - **Testing Expert** (`expert-testing`) - Test strategies, patterns, coverage analysis (8 knowledge files)
  - **Data Privacy Expert** (`expert-data-privacy`) - GDPR, HIPAA, CCPA compliance, privacy best practices (10 knowledge files)
  - **Accessibility Expert** (`expert-accessibility`) - WCAG 2.1/2.2, ARIA patterns, screen reader compatibility (9 knowledge files)
  - **User Experience Expert** (`expert-user-experience`) - UX principles, usability heuristics, interaction design (8 knowledge files)
  - **Code Quality Expert** (`expert-code-quality`) - Code quality analysis and maintainability
  - **Software Architecture Expert** (`expert-software-architecture`) - Architecture patterns and design principles
  - **Development Workflow Expert** (`expert-devops`) - DevOps practices and CI/CD
  - **Documentation Expert** (`expert-documentation`) - Documentation and knowledge management
  - **AI Agent Framework Expert** (`expert-ai-frameworks`) - AI agent frameworks and patterns
  - **Agent Learning Expert** (`expert-agent-learning`) - Agent learning best practices (3 knowledge files)
  - **Phase 5: High Priority Built-in Experts** - 4 new production-focused experts
    - **Observability & Monitoring Expert** (`expert-observability`) - Distributed tracing, metrics, logging, APM tools, SLO/SLI/SLA, alerting patterns, OpenTelemetry (8 knowledge files)
    - **API Design & Integration Expert** (`expert-api-design`) - RESTful API design, GraphQL patterns, gRPC best practices, API versioning, rate limiting, API gateway patterns, API security, contract testing (8 knowledge files)
    - **Cloud & Infrastructure Expert** (`expert-cloud-infrastructure`) - Cloud-native patterns, containerization, Kubernetes, infrastructure as code, serverless architecture, multi-cloud strategies, cost optimization, disaster recovery (8 knowledge files)
    - **Database & Data Management Expert** (`expert-database`) - Database design, SQL optimization, NoSQL patterns, data modeling, migration strategies, scalability patterns, backup and recovery, ACID vs CAP (8 knowledge files)
  - Total: 16 built-in experts with 83 knowledge base files (~320,000+ words of expert knowledge) across 16 technical domains

- **Dual-Layer Expert Architecture**
  - Built-in experts (framework-controlled, immutable, technical domains)
  - Customer experts (user-controlled, configurable, business domains)
  - Automatic priority system (technical domains prioritize built-in, business domains prioritize customer)
  - Weighted consultation with 51% primary authority

- **Enhanced Expert Registry**
  - `BuiltinExpertRegistry` - Manages framework-controlled built-in experts
  - Auto-loading of built-in experts on initialization
  - Priority-based consultation (`prioritize_builtin` parameter)
  - Automatic domain classification (technical vs business)
  - Enhanced `ExpertRegistry.consult()` with priority system

- **Agent Integration Patterns**
  - `ExpertSupportMixin` - Easy-to-use mixin for agent expert support
  - `_consult_builtin_expert()` - Convenience method for technical domains
  - `_consult_customer_expert()` - Convenience method for business domains
  - Automatic expert support initialization
  - Tester agent integrated as example

- **Comprehensive Documentation**
  - [Built-in Experts Guide](docs/BUILTIN_EXPERTS_GUIDE.md) - Complete guide to all built-in experts
  - [Expert Knowledge Base Guide](docs/EXPERT_KNOWLEDGE_BASE_GUIDE.md) - Knowledge base structure and best practices
  - [Migration Guide 2.0](docs/MIGRATION_GUIDE_2.0.md) - Step-by-step migration from 1.x to 2.0
  - Updated [API Documentation](docs/API.md) with new expert system APIs

- **Comprehensive Testing**
  - 15 comprehensive tests for dual-layer expert system
  - Tests for domain classification, priority system, consultation flow
  - All tests passing

### Changed
- **Expert Registry** - Now auto-loads built-in experts by default (`load_builtin=True`)
- **BaseExpert** - Supports built-in knowledge bases via `_builtin_knowledge_path`
- **Consultation API** - Enhanced with `prioritize_builtin` parameter and automatic domain detection
- **Expert Selection** - Automatic priority based on domain type (technical vs business)
- **Built-in Experts Guide** - Updated to version 2.0.0 with all 16 built-in experts documentation
- **Technical Domains** - Added 4 new technical domains: `observability-monitoring`, `api-design-integration`, `cloud-infrastructure`, `database-data-management`
- **Agent Integration** - Enhanced agent expert support matrix with Phase 5 experts (Architect, Implementer, Designer, Ops, Reviewer, Tester agents)

### Technical Details
- Built-in knowledge bases located in `tapps_agents/experts/knowledge/`
- Customer knowledge bases continue to use `.tapps-agents/knowledge/`
- Technical domains: security, performance-optimization, testing-strategies, code-quality-analysis, software-architecture, development-workflow, data-privacy-compliance, accessibility, user-experience, documentation-knowledge-management, ai-agent-framework, agent-learning, observability-monitoring, api-design-integration, cloud-infrastructure, database-data-management
- All other domains are business domains (customer experts prioritized)

### Breaking Changes
- **None** - Fully backward compatible with version 1.x
- Existing expert configurations continue to work
- Old consultation API still functional (with deprecation warnings)

### Migration
- See [Migration Guide 2.0](docs/MIGRATION_GUIDE_2.0.md) for detailed migration instructions
- No code changes required for existing implementations
- Built-in experts automatically available
- Optional: Add `ExpertSupportMixin` to agents for enhanced integration

## [1.6.0] - 2025-12-10

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

## [1.6.1] - 2025-12-10

### Changed
- **Dependencies Updated to Latest 2025 Stable Versions**
  - pytest: 8.4.2 → 9.0.2 (major version upgrade)
  - pytest-asyncio: 0.26.0 → 1.3.0 (major version upgrade)
  - pylint: 4.0.1 → 4.0.4
  - coverage: 7.10.6 → 7.13.0
  - black: 25.1.0 → 25.12.0
  - ruff: 0.14.5 → 0.14.8
  - mypy: 1.18.1 → 1.19.0
  - pytest-httpx: 0.35.0 → 0.36.0 (pytest 9.x compatibility)
  - All other dependencies updated to latest stable versions
  - See [requirements.txt](requirements.txt) for complete list

- **Test Suite Performance Optimization**
  - Disabled coverage by default in pytest.ini (2-5x faster test execution)
  - Run only unit tests by default (3-10x faster for daily development)
  - Added progress indicators to long-running tests for better visibility
  - Test suite now runs in ~4-8 seconds (unit tests) vs ~120-240 seconds (with coverage)
  - See [Test Performance Guide](docs/TEST_PERFORMANCE_GUIDE.md) for details

### Fixed
- Resolved dependency conflict with pytest-httpx for pytest 9.x compatibility
- Updated GitHub repository URLs to wtthornton/TappsCodingAgents
- Updated project structure documentation in README.md
- Fixed project context reference in README.md
- Updated Skills installation instructions across documentation
- Fixed Unicode encoding issues in test progress indicators for Windows compatibility

### Documentation
- Updated all documentation to reflect latest dependency versions
- Updated project structure in README.md
- Updated Skills installation instructions in QUICK_START.md and DEVELOPER_GUIDE.md
- Updated repository URLs across all documentation files
- Added comprehensive [Test Performance Guide](docs/TEST_PERFORMANCE_GUIDE.md) with optimization strategies

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
| 2.0.3 | Jan 2025 | Fixed RAG knowledge base directory creation for URL-based domain names (Windows compatibility) |
| 2.0.2 | Jan 2026 | Documentation review and updates; version consistency improvements |
| 2.0.1 | Dec 2025 | Packaged init assets for PyPI installs; docs alignment; doctor targets aligned |
| 2.0.0 | Jan 2026 | Complete Built-in Expert System (16 experts), Dual-Layer Architecture, All 7 Cursor AI Integration Phases Complete |
| 1.6.1 | Dec 2025 | Dependencies Updated, Test Performance Optimization |
| 1.6.0 | Dec 2025 | Enhancer Agent - Prompt Enhancement Utility with Expert Integration |
| 1.5.0 | Dec 2025 | Phase 6 Complete - Modern Quality Analysis (Ruff, mypy, TypeScript, multi-service, dependencies) |
| 1.4.0 | Dec 2025 | Phase 6.1-6.3 - Reporting, Type Checking, Ruff Integration |
| 1.3.0 | Dec 2025 | Phase 5 Complete - Context7 Integration |
| 1.2.0 | Dec 2025 | Phase 3-4 - Examples and Workflow Selection |
| 1.1.0 | Dec 2025 | Enhanced Features and Industry Experts |
| 1.0.0 | Dec 2025 | Core Framework |

---

## [2.2.0] - Unreleased

### Planned Features

- Enhanced test coverage for Phase 6 components
- TypeScript support integration in Implementer and Tester agents
- Advanced analytics dashboard enhancements
- Vector DB integration for RAG (if needed)
- Additional built-in experts based on community feedback

---
**Note**: This changelog is maintained according to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) principles.

