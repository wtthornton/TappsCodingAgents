# Deployment Guide

**Version**: 2.0.5  
**Last Updated**: January 2026

## Overview

TappsCodingAgents is a Python package that you typically run as a CLI tool against a project directory.

## Prerequisites

- Python 3.13+ (recommended: latest stable Python)
- pip
- (Optional, headless only) Ollama for local LLM execution via MAL

## Local Installation

```bash
git clone https://github.com/wtthornton/TappsCodingAgents.git
cd TappsCodingAgents

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -e .

python -m tapps_agents.cli --help
```

## Cursor-first note

When using TappsCodingAgents inside Cursor (Skills / Background Agents), Cursor uses the developer’s configured model.
The framework runs tools-only in that environment.

If you explicitly want MAL for a headless CLI run, set:

```bash
export TAPPS_AGENTS_MODE=headless
```

## Configuration

Configuration is optional. If you want to customize behavior, create:

- `.tapps-agents/config.yaml`

Recommended (creates config + Cursor integration assets):

```bash
python -m tapps_agents.cli init
```

Or start from the template (manual copy):

```bash
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

See `docs/CONFIGURATION.md`.

## Docker (example)

If you want a containerized environment to run the CLI:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . /app
RUN pip install -e .
CMD ["python", "-m", "tapps_agents.cli", "--help"]
```

Build and run:

```bash
docker build -t tapps-agents:local .
docker run --rm tapps-agents:local
```

To run against a mounted workspace:

```bash
docker run --rm -v %CD%:/workspace -w /workspace tapps-agents:local \
  python -m tapps_agents.cli reviewer score example_bug.py
```

## CI/CD

In CI, prefer:

- `python -m tapps_agents.cli reviewer lint ...`
- `python -m tapps_agents.cli reviewer type-check ...`
- `python -m tapps_agents.cli reviewer report ...`

Reports default to `reports/quality/`.

### CI Environment Variables

For production CI environments, configure:

```bash
# Enable structured logging (JSON format)
export TAPPS_AGENTS_STRUCTURED_LOGGING=true

# Set runtime mode explicitly
export TAPPS_AGENTS_MODE=headless

# Optional: Set trace ID for distributed tracing
export CURSOR_TRACE_ID=${CI_PIPELINE_ID}
```

## Production Readiness Checklist

Before deploying to production, ensure:

- [ ] **Logging & Monitoring**: Structured logging enabled (`TAPPS_AGENTS_STRUCTURED_LOGGING=true`)
- [ ] **Error Handling**: Error redaction verified (no secrets in logs/artifacts)
- [ ] **Artifact Retention**: Configured retention policies for `.tapps-agents/` artifacts
- [ ] **Quality Gates**: Quality thresholds configured in workflows (if applicable)
- [ ] **Configuration**: Production config file validated and tested
- [ ] **Dependencies**: All required tools available (Ruff, mypy, pytest, etc.)
- [ ] **Credentials**: Context7/MAL credentials configured securely (if used)
- [ ] **Worktree Cleanup**: Automated cleanup configured for old worktrees
- [ ] **Metrics**: Analytics collection enabled and monitored

## Support Boundaries

### Required Components

- **Python 3.13+**: Framework requires Python 3.13 or later
- **Core Agents**: All 13 workflow agents are required for full functionality
- **Workflow Engine**: Required for workflow execution

### Optional Components (Graceful Degradation)

- **Context7**: Optional library documentation cache. If unavailable, agents continue without it.
- **MAL (Model Abstraction Layer)**: Optional for headless mode. Required only if running outside Cursor.
- **Playwright**: Optional for browser automation. Some features may be limited without it.
- **External Quality Tools**: Ruff, mypy, pytest are optional but recommended for quality checks.

### Best-Effort Features

- **Expert System**: Built-in experts are always available. Custom experts are best-effort.
- **Workflow Recommendations**: Auto-detection is best-effort; manual workflow selection always works.
- **Cache Warming**: Context7 cache warming is best-effort and non-blocking.

## Related Documentation

- `docs/TROUBLESHOOTING.md` - Common issues and solutions
- `docs/CONFIGURATION.md` - Complete configuration reference
- `docs/API.md` - Python API and CLI usage
- `docs/ARCHITECTURE.md` - System architecture overview
