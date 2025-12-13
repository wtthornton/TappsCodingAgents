# Deployment Guide

**Version**: 2.0.0  
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

## Related Documentation

- `docs/TROUBLESHOOTING.md`
- `docs/CONFIGURATION.md`
