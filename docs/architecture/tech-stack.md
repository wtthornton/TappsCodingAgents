---
title: Technology Stack
version: 3.6.1
status: active
last_updated: 2026-02-05
tags: [architecture, tech-stack, dependencies]
---

# Technology Stack

This document provides an overview of the technology stack used in TappsCodingAgents.

## Runtime

- **Python**: 3.12+ (required; 3.13 recommended)
- **Package Manager**: pip (with pyproject.toml as authoritative source)
- **Build System**: setuptools

## Core Framework Dependencies

### Essential Libraries

- **pydantic** (≥2.12.5): Data validation and settings management
- **httpx** (≥0.28.1): Async HTTP client for API calls
- **pyyaml** (≥6.0.3): YAML parsing for workflow definitions
- **aiohttp** (≥3.13.3): Async HTTP server/client (alternative to httpx)
- **psutil** (≥7.2.2): System and process utilities
- **rich** (≥14.3.2): CLI UX (progress spinners, live updates)
- **aiofiles** (≥25.1.0): Async file operations (optional with fallback)

### Code Analysis (Runtime)

- **radon** (≥6.0.1): Code complexity analysis
- **bandit** (≥1.9.3): Security vulnerability scanning
- **coverage** (≥7.13.3): Code coverage analysis

### Reporting

- **jinja2** (≥3.1.6): Template engine for report generation
- **plotly** (≥6.5.2): Interactive charts and graphs (optional reporting extra)

### Dependency Management

- **packaging** (≥23.2,<27): Version and dependency management
  - Constrained to avoid conflicts with transitive dependencies (e.g., langchain-core)

## Development Dependencies

### Code Formatting

- **ruff** (≥0.15.0,<1.0): Fast Python linter and formatter (10-100x faster than alternatives)

### Type Checking

- **mypy** (≥1.19.1,<2.0): Static type checker
- **types-PyYAML** (≥6.0.12.20250915): Type stubs for PyYAML

### Testing

- **pytest** (≥9.0.2): Testing framework
- **pytest-asyncio** (≥1.3.0): Async test support
- **pytest-cov** (≥7.0.0): Coverage plugin
- **pytest-mock** (≥3.15.1): Mocking utilities
- **pytest-timeout** (≥2.4.0): Test timeout management
- **pytest-xdist** (≥3.8.0): Parallel test execution
- **pytest-sugar** (≥1.1.1): Enhanced terminal output
- **pytest-html** (≥4.1.1): HTML test reports
- **pytest-rich** (≥0.2.0): Rich output for pytest

### Security & Dependency Management

- **pip-audit** (≥2.10.0): Dependency vulnerability scanning
- **pip-tools** (≥7.5.2): Lock file generation

### Dependency Analysis (Optional Extra)

- **pipdeptree** (≥2.30.0): Dependency tree visualization
  - Note: Requires packaging≥25, which conflicts with packaging<25 constraint
  - Install separately: `pip install -e ".[dependency-analysis]"`

## External Services

### Context7

- **Purpose**: Library documentation lookup
- **Integration**: MCP server (Model Context Protocol)
- **Caching**: KB-first caching with async LRU cache
- **Configuration**: `.cursor/mcp.json`

### Playwright (Optional)

- **Purpose**: Browser automation
- **Integration**: MCP server (auto-detected)
- **Usage**: E2E testing, web scraping

## Architecture Patterns

### Instruction-Based Architecture

- **Model**: Agents prepare structured instruction objects
- **Execution**: Instructions executed via Cursor Skills
- **Runtime**: Cursor handles all LLM operations (no local LLM required)

### YAML-First Workflows

- **Definition**: YAML files with strict schema enforcement
- **Parsing**: `tapps_agents/workflow/parser.py`
- **Execution**: Parallel execution with dependency resolution

### Expert System

- **Built-in Experts**: 16 technical domain experts
- **Industry Experts**: Project-defined business experts
- **RAG Integration**: File-based and vector-based RAG support

## Platform Support

- **Primary**: Windows (developed and tested)
- **Secondary**: Linux, macOS (compatible)
- **Encoding**: UTF-8 (with Windows CP1252 fallback handling)

## Performance Optimizations

### 2025 Enhancements

- **Async LRU Cache**: Non-blocking cache with background write queue
- **Circuit Breaker**: Automatic failure handling for external services
- **Cache Pre-warming**: Automatic dependency detection and cache population
- **Lock Timeout Optimization**: Reduced from 30s → 5s (3s for cache store)

### Parallel Execution

- **Workflow Steps**: Up to 8 concurrent steps
- **Test Execution**: pytest-xdist for parallel test runs
- **TaskGroup**: Structured concurrency with asyncio.TaskGroup

## Related Documentation

- **Architecture Overview**: `docs/ARCHITECTURE.md`
- **Configuration**: `docs/CONFIGURATION.md`
- **Dependency Policy**: `docs/DEPENDENCY_POLICY.md`
- **Performance Guide**: `docs/architecture/performance-guide.md`

---

**Last Updated:** 2026-02-05
**Maintained By:** TappsCodingAgents Team
