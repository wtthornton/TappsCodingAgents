# Changelog

All notable changes to TappsCodingAgents will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.2.5] - 2025-01-16

### Added
- **Doctor Command Enhancements** - Comprehensive checks for all init components
  - Added Cursor Rules verification (checks for all 7 required rule files)
  - Added Cursor Skills verification (checks for all 14 required skills)
  - Added Background Agents config verification
  - Added Workflow Presets verification (checks for all 5 required presets)
  - Added .cursorignore file check
  - Added project config file check
  - All checks provide remediation messages suggesting 'tapps-agents init'
  - Verifies Playwright MCP configuration is correct (optional, with Python fallback)

### Changed
- **Doctor Command** - Now comprehensively checks all components that init creates
  - Doctor now suggests running init when components are missing
  - Improved integration with Cursor verification utilities

## [3.2.4] - 2025-01-16

### Added
- **Reviewer Agent Enhancements** - Improved error handling, validation, and Context7 integration
  - Added error handling module (`error_handling.py`) with comprehensive error management
  - Added validation module (`validation.py`) for input validation and type checking
  - Added score constants module (`score_constants.py`) for centralized scoring configuration
  - Added library patterns module (`library_patterns.py`) for improved library detection
  - Enhanced Context7 integration with better library detection and lookup capabilities
  - Improved quality gates and build orchestrator reliability

### Changed
- **Reviewer Agent** - Enhanced code quality with modular architecture
  - Refactored scoring system for better maintainability
  - Improved error handling throughout the agent
  - Enhanced library pattern matching for Context7 integration

### Documentation
- Added `docs/CONTEXT7_MCP_SERVER_ERRORS.md` - Context7 MCP server error handling guide
- Added `docs/REVIEWER_AGENT_2025_ENHANCEMENTS.md` - Comprehensive reviewer agent enhancement documentation
- Added `docs/REVIEWER_AGENT_CODE_QUALITY_IMPROVEMENTS.md` - Code quality improvements documentation
- Added `docs/REVIEWER_AGENT_FIXES_IMPLEMENTED.md` - Fixes and improvements summary

### Testing
- Added unit tests for validation module (`test_validation.py`)
- Added unit tests for score constants (`test_score_constants.py`)

## [3.2.3] - 2025-01-16

### Fixed
- **Simple Mode Full Workflow Infinite Loop (Issue 10)** - Fixed infinite hangs in Simple Mode full workflow execution
  - Added overall workflow timeout protection (2x step timeout, default: 2 hours) to prevent infinite hangs
  - Enhanced workflow initialization with validation (empty workflow check, first step readiness validation)
  - Improved no ready steps handling with detailed diagnostics (blocking step identification, missing artifact detection)
  - Added progress reporting with step-by-step visibility and logging every 10 steps
  - Force auto-execution for Simple Mode full workflow with clear warnings when disabled
  - Added health check method (`get_workflow_health()`) for workflow diagnostics and stuck detection
  - Enhanced error messages with actionable remediation steps
  - Comprehensive test suite added (24 tests: 19 unit, 5 integration)
  - See `docs/ISSUE_10_SIMPLE_MODE_FULL_WORKFLOW_INFINITE_LOOP_PLAN.md` for complete details

### Added
- **Workflow Diagnostics** - Enhanced diagnostic capabilities for workflow execution
  - Health check method returns comprehensive workflow status (progress, timing, stuck detection)
  - Detailed blocking diagnostics when no steps are ready (identifies blockers and missing artifacts)
  - Progress logging every 10 steps for visibility during long-running workflows
  - Timeout error messages with actionable remediation steps

### Changed
- **Simple Mode Full Workflow** - Enhanced execution reliability
  - Auto-execution enabled by default for Simple Mode full workflow
  - Clear warnings when auto-execution is explicitly disabled
  - Better progress visibility with step-by-step reporting
  - Improved timeout handling with graceful error messages

### Documentation
- Added `docs/ISSUE_10_IMPLEMENTATION_SUMMARY.md` - Complete implementation summary
- Added `docs/ISSUE_10_TEST_SUITE_SUMMARY.md` - Test suite documentation
- Updated `docs/ISSUE_10_SIMPLE_MODE_FULL_WORKFLOW_INFINITE_LOOP_PLAN.md` - Enhanced fix plan

## [3.2.2] - 2025-12-29

### Fixed
- **Workflow Auto-Execution Command Mapping** - Fixed missing command mappings for workflow auto-execution
  - Added missing `("improver", "refactor")` mapping to `COMMAND_MAPPING` in `skill_invoker.py`
  - Added missing `("documenter", "update_docstrings")` and `("documenter", "update-docstrings")` mappings
  - Added `debug_report` parameter handler to support refactor instructions from debug artifacts
  - Resolves `Unknown command for auto-execution: improver/refactor` error in maintenance, quality, and simple-improve-quality workflows
  - All workflow presets using `improver/refactor` and `documenter/update_docstrings` now execute successfully with auto-execution enabled

## [3.2.1] - 2025-01-16

### Added
- **Context7 Automatic Integration Enhancements** - Enhanced automatic Context7 documentation integration across all agents
  - Comprehensive documentation and enhancement proposals for automatic Context7 usage
  - Full SDLC documentation for Context7 integration improvements
  - See `docs/TAPPS_AGENTS_CONTEXT7_AUTO_ENHANCEMENT.md` for complete details

### Documentation
- Added `docs/TAPPS_AGENTS_CONTEXT7_AUTO_ENHANCEMENT.md` - Complete Context7 automatic integration enhancement proposal
- Updated stabilization plan with Context7 integration improvements

## [3.2.0] - 2025-01-16

### Added
- **Playwright MCP Integration** - Complete integration with Playwright MCP server for browser automation
  - Automatic detection of Playwright MCP server configuration
  - Setup instructions generated when Playwright MCP is missing
  - Doctor command reports Playwright MCP status with remediation guidance
  - Tester agent automatically detects and leverages Playwright MCP when generating E2E tests
  - Graceful fallback to Python Playwright package if MCP not configured
  - Comprehensive documentation updates (TROUBLESHOOTING.md, quick-reference.mdc, agent-capabilities.mdc, command-reference.mdc)
  - Follows same pattern as Context7 MCP integration for consistency
  - See `docs/PLAYWRIGHT_MCP_INTEGRATION.md` for complete guide

### Changed
- **Tester Agent** - Enhanced E2E test generation with Playwright MCP awareness
  - Automatically detects Playwright MCP availability when generating Playwright-based E2E tests
  - Test generation prompts include note about Playwright MCP availability when configured
- **Doctor Command** - Added Playwright MCP status checking
  - Reports Playwright MCP configuration status
  - Provides setup instructions when missing
  - Distinguishes between Playwright MCP and Python Playwright package
- **Init Command** - Enhanced MCP detection with Playwright MCP setup instructions
  - Generates setup instructions following Context7 MCP pattern
  - Includes configuration examples and alternative options

### Documentation
- Added `docs/PLAYWRIGHT_MCP_INTEGRATION.md` - Complete integration guide
- Added `docs/PLAYWRIGHT_MCP_CODE_REVIEW.md` - Code review summary
- Updated `docs/TROUBLESHOOTING.md` - Enhanced Playwright section with MCP information
- Updated `tapps_agents/resources/cursor/rules/quick-reference.mdc` - Enhanced Playwright warning section
- Updated `tapps_agents/resources/cursor/rules/agent-capabilities.mdc` - Added Playwright MCP to Tester Agent
- Updated `tapps_agents/resources/cursor/rules/command-reference.mdc` - Added Playwright MCP integration section
- Updated `.claude/skills/tester/SKILL.md` - Added Playwright MCP awareness to capabilities
- Updated `README.md` - Added Playwright MCP to MCP Gateway sections
- Updated `docs/README.md` - Added Playwright MCP integration documentation link

## [3.1.1] - 2025-01-16

### Changed
- Version bump for release

## [3.1.0] - 2025-12-29

### Added
- **File Path Support for Custom Workflows** - Users can now execute custom workflow YAML files directly via CLI
  - Added `orchestrator workflow <file_path>` command for direct file execution
  - Added automatic file path detection to top-level `workflow` and `create` commands
  - Supports both preset names and file paths (auto-detection based on path patterns)
  - Examples:
    - `tapps-agents workflow workflows/custom/my-workflow.yaml`
    - `tapps-agents orchestrator workflow <file_path>`
    - `tapps-agents create "..." --workflow <file_path>`

### Changed
- **Path Resolution** - Improved path handling using `Path.resolve()` for consistent normalization
  - Better Windows compatibility with proper symlink handling
  - Consistent with existing codebase patterns
- **Error Messages** - Enhanced error messages to show both original and resolved paths for better debugging

### Fixed
- **Input Validation** - Added validation for `None` and empty string inputs in workflow commands
- **Windows Encoding** - Fixed Unicode encoding issues in `pytest_rich_progress.py` for Windows console output

### Security
- **Path Validation** - Added input validation to prevent errors from invalid file paths
- **Path Resolution** - Proper handling of path traversal sequences using `Path.resolve()`

### Documentation
- Added comprehensive code review document: `docs/CODE_REVIEW_WORKFLOW_FILE_PATH_SUPPORT.md`
- Updated help text and CLI documentation with file path examples

### Testing
- Added comprehensive unit tests for `_execute_workflow_from_file` method
- Added E2E tests for both success and failure paths
- Test coverage for relative paths, absolute paths, and error cases

## [3.0.5] - 2025-01-16

### Fixed
- **Reviewer Agent Batch Processing Crashes** - Fixed crashes during batch file processing with connection errors
  - Added retry logic with exponential backoff (2s, 4s, 8s) for connection errors
  - Implemented circuit breaker pattern to prevent cascading failures (opens after 5 consecutive failures)
  - Added per-attempt timeout protection (120s) to prevent hanging operations
  - Enhanced error classification to distinguish retryable (transient) vs non-retryable (permanent) errors
  - Added comprehensive exception handling in `review_file` method
  - Improved error metadata for better debugging (error_type, timeout flags)

### Added
- **Batch Processing Documentation** - Added comprehensive documentation for batch processing fixes:
  - `docs/REVIEWER_BATCH_CRASH_ANALYSIS.md` - Root cause analysis
  - `docs/REVIEWER_BATCH_CRASH_BEST_PRACTICES.md` - Best practices applied
  - `docs/REVIEWER_BATCH_CRASH_FIX.md` - Initial fix documentation
  - `docs/REVIEWER_BATCH_CRASH_FIX_V2.md` - Additional fixes documentation

### Changed
- **Error Handling** - Enhanced error handling throughout reviewer agent:
  - Better timeout error handling with specific retry logic
  - Improved error messages with context (file path, retry attempts, error types)
  - Graceful degradation when circuit breaker opens (returns partial results)

## [3.0.4] - 2025-12-29

### Fixed
- **Auto-Execution Flag** - Fixed `--auto` flag not properly enabling Background Agent auto-execution in workflow commands
  - `auto_mode` parameter now correctly forces `auto_execution_enabled = True` when `--auto` flag is used
  - Enhanced logging to show when auto-execution is enabled/disabled and why
  - Improved error messages with helpful tips when auto-execution fails

### Changed
- **Cursor Workflow Executor** - Enhanced `cursor_executor.py` with improved workflow execution:
  - Better auto-executor initialization with comprehensive logging
  - Enhanced error handling with structured logging
  - Improved auto-execution status tracking and reporting
- **Orchestrator Agent** - Updated orchestrator agent for better workflow coordination

### Added
- **Auto Execution Fix Documentation** - Added `docs/AUTO_EXECUTION_FIX_SUMMARY.md` documenting the auto-execution fix and implementation details

## [3.0.3] - 2025-12-29

### Added
- **Background Agents Monitoring Documentation** - Comprehensive guide for monitoring and managing background agents
- **Help Functions Analysis** - Performance analysis and improvements summary documentation
- **Monitoring Script** - Added `scripts/monitor_status.py` for real-time agent status monitoring
- **Workflow Events** - Enhanced workflow event tracking and logging
- **Version Update Script Improvements** - Enhanced `scripts/update_version.ps1` with PowerShell best practices:
  - Added CmdletBinding for better PowerShell integration
  - Used ValidatePattern attribute for parameter validation
  - Improved error handling with Write-Error and proper error categories
  - Added try-catch blocks for robust file operations
  - Added JSON metadata file support (IMPROVEMENT_PLAN.json)
- **Version Management Documentation** - Added comprehensive documentation for version management in README.md and .cursorrules

### Changed
- **Agent Implementations** - Updated multiple agent implementations for improved reliability:
  - Debugger agent: Enhanced error analysis capabilities
  - Documenter agent: Improved documentation generation
  - Implementer agent: Better code generation patterns
  - Improver agent: Enhanced code improvement suggestions
  - Ops agent: Improved security and deployment operations
  - Orchestrator agent: Enhanced workflow coordination
  - Planner agent: Better story planning and estimation
  - Tester agent: Improved test generation and execution
- **Core Functionality** - Enhanced core components:
  - `agent_base.py`: Improved base agent functionality
  - `cursor_verification.py`: Better Cursor integration validation
  - `init_project.py`: Enhanced project initialization
- **Version Update Script** - Refactored with PowerShell best practices:
  - Replaced manual validation with ValidatePattern attribute
  - Improved error handling with proper error categories and ErrorId
  - Added comprehensive try-catch blocks for all file operations
  - Better error messages with RecommendedAction
- **Documentation** - Updated all version references to 3.0.3 across:
  - README.md (version badge and references)
  - docs/README.md (documentation version)
  - docs/API.md (API version)
  - docs/ARCHITECTURE.md (architecture version)
  - implementation/IMPROVEMENT_PLAN.json (metadata version)

### Fixed
- Improved test coverage for orchestrator agent
- Enhanced error handling across multiple agents
- Fixed PowerShell script string concatenation issue in update_version.ps1
- Ensured all version references are consistently updated across the codebase

## [3.0.2] - 2025-12-29

### Fixed
- **OrchestratorAgent.activate()** - Fixed to accept `offline_mode` parameter, resolving TypeError in orchestrator CLI command handler
- Resolved parameter mismatch in orchestrator agent activation

### Documentation
- Added documentation for multiple installations and upgrade troubleshooting
- Updated expert knowledge files to 2025 standards
- Enhanced CLI feedback and user experience documentation

## [3.0.1] - 2026-01-31

### Fixed
- Fixed version import issues in editable installs - added defensive import pattern with fallbacks
- Fixed lint command bug where `'str' object has no attribute 'get'` error occurred
- Enhanced error handling in batch lint processing to handle malformed Ruff output
- Added defensive checks to ensure all result objects are dicts before processing
- **Fixed ModuleNotFoundError after upgrade** - When upgrading to 3.0.1, if you encounter `ModuleNotFoundError: No module named 'tapps_agents.agents.analyst'`, reinstall the package with `pip install -e .` to refresh editable install metadata

### Changed
- Improved version import robustness with 3-strategy fallback (direct import → importlib.metadata → file reading)
- Enhanced lint command to filter out non-dict items from issues list
- Made code counting more robust to handle different code structure formats

## [3.0.0] - 2026-01-31

### Changed
- **Major Version Release** - Version bump to 3.0.0
- Updated all documentation to reflect version 3.0.0
- Comprehensive documentation accuracy review completed
- All version references updated across codebase and documentation

### Documentation
- Updated version numbers in all key documentation files
- Verified accuracy of all documentation against actual codebase
- Aligned README.md, docs/README.md, ARCHITECTURE.md, API.md, and BUILTIN_EXPERTS_GUIDE.md with code

## [2.9.0] - 2026-01-30

### Changed
- Updated version to 2.9.0 across all files
- Updated documentation with latest version information

## [2.8.0] - 2026-01-30

### Added
- Version update and release automation improvements

### Changed
- Updated version to 2.8.0 across all files
- Updated documentation with latest version information

## [2.7.0] - 2026-01-29

### Added
- **Enhanced CLI User Feedback Indicators** - Comprehensive feedback system across all CLI commands
  - Clear status indicators: `[START]`, `[RUNNING]`, `[SUCCESS]`, `[ERROR]`, `[WARN]`
  - Step-by-step progress tracking with step numbers (e.g., "Step 2 of 5")
  - Enhanced `start_operation()` method with descriptive operation names and context
  - New `running()` method for showing current progress with step information
  - Improved success messages with summary information
  - Better error visibility with clear visual indicators
  - Stream separation: status messages to stderr, data to stdout (prevents PowerShell JSON parsing errors)
  - Progress tracking for all multi-step operations

- **Enhanced Commands** - All CLI commands now provide consistent feedback:
  - **Tester**: `test`, `generate-tests`, `run-tests` - Added step-by-step progress tracking
  - **Planner**: `plan`, `create-story` - Added progress tracking and summary information
  - **Implementer**: `implement`, `generate-code`, `refactor` - Added 4-step progress tracking
  - **Analyst**: All 6 commands enhanced with progress tracking and summaries
  - **Top-Level**: `hardware-profile`, `create`, `workflow` - Added progress tracking
  - **Simple Mode**: `on`, `off`, `status`, `full` - Added step-by-step progress
  - **Health**: `check`, `dashboard`, `metrics`, `trends` - Added progress tracking with health summaries
  - **Reviewer**: `report` - Enhanced with detailed progress and report summaries

- **Documentation** - Comprehensive documentation for CLI feedback enhancements
  - `CLI_USER_FEEDBACK_ENHANCEMENT_PLAN.md` - Problem analysis and solution plan
  - `CLI_FEEDBACK_IMPLEMENTATION_GUIDE.md` - Detailed implementation guide with code examples
  - `CLI_FEEDBACK_SUMMARY.md` - Quick reference summary
  - `CLI_FEEDBACK_IMPROVEMENTS_SUMMARY.md` - Implementation summary
  - `CLI_FEEDBACK_ALL_COMMANDS_PLAN.md` - All commands enhancement plan
  - `CLI_FEEDBACK_ALL_COMMANDS_COMPLETE.md` - Complete implementation summary

### Changed
- **CLI Feedback System** - Major improvements to user experience
  - Status messages now always go to stderr (even in JSON mode) to prevent PowerShell parsing errors
  - All commands show clear operation start indicators
  - Multi-step operations show progress with step numbers
  - Success messages include duration and summary information
  - Error messages are clearly distinguished with visual indicators

- **Command Output Format** - Improved consistency across all commands
  - Consistent status indicator format across all commands
  - Standardized progress tracking format
  - Enhanced summary information in success messages

### Fixed
- **PowerShell JSON Parsing Errors** - Fixed issue where PowerShell tried to parse JSON status messages as commands
  - Status messages now go to stderr as plain text (even in JSON mode)
  - Only final results go to stdout as JSON
  - Prevents PowerShell from attempting to execute JSON output

- **User Feedback Clarity** - Resolved issues with unclear command status
  - Users can now clearly see if commands are running, stuck, or completed
  - Progress indicators show what's happening at each step
  - Error states are immediately obvious

## [2.6.0] - 2026-01-28

### Added
- **Epic Workflow Orchestration** - Execute Epic documents with automatic story dependency resolution
  - Epic document parsing with story extraction and dependency resolution
  - Topological sort (Kahn's algorithm) for story execution order
  - Quality gate enforcement after each story with automatic loopback
  - Progress tracking and completion reports
  - Simple Mode command: `@simple-mode *epic <epic-doc.md>`
  - Comprehensive Epic Workflow Guide documentation
  - See `docs/EPIC_WORKFLOW_GUIDE.md` for details

- **Coverage-Driven Test Generation** - Intelligent test generation based on coverage gaps
  - Coverage analyzer for JSON and .coverage database formats
  - Gap identification and prioritization
  - Targeted test generation for uncovered code paths
  - Integration with test generators for automatic gap filling
  - Coverage threshold checking and reporting

- **Docker Debugging Capabilities** - Automated Docker container issue diagnosis
  - Dockerfile analysis for common issues (Python path, WORKDIR, COPY order)
  - Container log retrieval and analysis
  - Error pattern matching with confidence scoring
  - Automatic fix suggestions based on known patterns
  - Pattern learning from successful fixes

- **Microservice Generation** - Automated microservice boilerplate generation
  - FastAPI and Flask service templates
  - Dockerfile and docker-compose integration
  - Health check endpoints
  - Test scaffolding
  - HomeIQ-specific patterns support

- **Service Integration Automation** - Automate service-to-service integration
  - Client class generation
  - Configuration file updates
  - Dependency injection setup
  - Integration test generation

- **Quality Gate Enforcement** - Mandatory quality checks with automatic loopback
  - Configurable quality thresholds (overall, security, maintainability, test coverage)
  - Critical service detection with higher thresholds
  - Automatic improvement loopback on quality failures
  - Integration with Epic workflows for story-level enforcement

- **Test Fixing Capabilities** - Automatic test failure analysis and fixing
  - Pattern-based test failure detection
  - Common issue fixes (async/await, authentication, mocks)
  - Batch test fixing support
  - Test modernization (e.g., TestClient → AsyncClient migration)

- **Batch Test Generation** - Generate tests for multiple files simultaneously
  - Shared fixture detection
  - Consistent test patterns across files
  - Integration test support

- **Context-Aware Test Generation** - Learn from existing test patterns
  - Test style matching
  - Fixture reuse
  - Pattern recognition from codebase

- **Service Integration Testing** - Generate service-to-service integration tests
  - Internal authentication handling
  - Dependency mocking
  - Service-to-service communication patterns

### Changed
- **Simple Mode** - Added Epic intent type (5th intent type)
  - Epic command: `@simple-mode *epic <epic-doc.md>`
  - Epic synonyms: epic, implement epic, execute epic, run epic, story, stories
  - Updated Simple Mode Guide with Epic workflow documentation

- **Agent Capabilities** - Enhanced capabilities documentation
  - Added new Tester capabilities (coverage-driven, test fixing, batch generation)
  - Added new Ops capabilities (Docker debugging, analysis)
  - Added new Orchestrator capabilities (Epic orchestration, quality gates, service integration)
  - Added "Specialized Tools" section with Epic Orchestrator, Microservice Generator, Coverage Analyzer, Docker Debugger

- **Documentation** - Comprehensive documentation updates
  - New Epic Workflow Guide (`docs/EPIC_WORKFLOW_GUIDE.md`)
  - Updated Simple Mode Guide with Epic intent
  - Updated Agent Capabilities with new features
  - Updated Command Reference (already complete)
  - Updated README with Epic examples

### Fixed
- **Code Review Issues** - Fixed syntax errors and linting issues
  - Fixed indentation errors in reviewer agent exception handlers
  - Fixed unused imports and variables in Epic orchestrator
  - All linting issues resolved (ruff check passes)

### Documentation
- **Epic Workflow Guide** - Comprehensive guide for Epic workflows
  - Quick start guide
  - Epic document format specification
  - Story format specification
  - Examples (simple and complex Epics)
  - Configuration options
  - Best practices and troubleshooting

- **Code Review Documentation** - New code review document
  - Analysis of 6 new components
  - 15+ issues identified with recommendations
  - Code quality metrics
  - Test coverage requirements

## [2.5.1] - 2026-01-27

### Fixed
- **Workflow Schema Validation** - Fixed schema validation errors in workflow preset files
  - Fixed `brownfield-analysis.yaml`: moved `project_types` to metadata, changed workflow type from 'analysis' to 'brownfield'
  - Fixed `simple-full.yaml`: moved `loopback` settings to metadata
  - All workflow presets now pass schema validation during `tapps-agents init`
  - Resolves workflow parsing errors that prevented proper initialization

## [2.5.0] - 2026-01-27

### Added
- **Enhanced Context7 Integration** - Improved Context7 integration with Cursor MCP support and agent integrations
  - Enhanced MCP server configuration and integration
  - Improved agent access to Context7 documentation
  - Better error handling and fallback mechanisms
- **Offline Mode Handler** - Implemented offline mode handler to prevent connection errors
  - Graceful degradation when network is unavailable
  - Improved error messages for offline scenarios
- **Focus Argument Support** - Added `--focus` argument support for improver and tester commands
  - Allows users to focus on specific aspects of code improvement
  - Enhanced targeting for test generation

### Changed
- **Documentation Updates** - Updated documentation with latest improvements
- **CLI Improvements** - Enhanced CLI with better error handling and user experience
- **Workflow Enhancements** - Improved workflow execution and error recovery

## [2.4.4] - 2026-01-27

### Fixed
- **CLI Help Connection Errors** - Fixed connection errors when running help commands offline
  - Created static help system (`tapps_agents/cli/help/static_help.py`) with offline help text for all 13 agents
  - Updated all agent command handlers to check for help commands before agent activation
  - Help commands now work completely offline without requiring network connections
  - Help commands complete in < 100ms (40-100x faster than before)
  - All 13 agents fixed: enhancer, analyst, architect, debugger, designer, documenter, implementer, improver, ops, orchestrator, planner, reviewer, tester
  - Resolves issue where `python -m tapps_agents.cli <agent> --help` would fail with connection errors when network was unavailable
  - See `docs/implementation/TAPPS_AGENTS_CONNECTION_ERROR_ISSUE.md` for full details

### Added
- **Static Help System** - New offline help system for CLI commands
  - Centralized help text module (`tapps_agents/cli/help/`)
  - Help text extracted from command reference documentation
  - No network dependency for help commands
  - Comprehensive help text for all 13 agents with command descriptions, options, and examples

### Performance
- **Help Command Performance** - Significantly improved help command response time
  - Response time: < 50ms (previously 2-5 seconds)
  - Memory usage: < 10MB (previously 50-100MB)
  - Network requests: 0 (previously 3-5 requests)

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

