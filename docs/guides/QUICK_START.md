---
title: Quick Start Guide
version: 3.5.21
status: active
last_updated: 2026-01-20
tags: [quick-start, getting-started, setup]
---

# Quick Start Guide

Get up and running with TappsCodingAgents in about 5–10 minutes.

## 1. Install

Requires **Python 3.13+** (`python --version`).

```bash
# Linux/macOS:
python3.13 -m pip install -e .
# or: pip install -e .

# Windows (if 3.13 is not default):
py -3.13 -m pip install -e .
```

Or from PyPI: `pip install tapps-agents`

Optionally: `python scripts/check_prerequisites.py` before installing.

After installing: `tapps-agents doctor` or `python -m tapps_agents.cli doctor` to verify.

### Windows

```powershell
py -3.13 --version
py -3.13 -m pip install -e .
py -3.13 -m tapps_agents.cli init
```

### Linux/macOS

```bash
python3.13 --version
python3.13 -m pip install -e .
python3.13 -m tapps_agents.cli init
```

## 2. Initialize Cursor Integration

Run `init` from your **project root**, not from the TappsCodingAgents framework directory.

```bash
# From your project (tapps-agents or python -m tapps_agents.cli if command not found):
tapps-agents init
# Or: python -m tapps_agents.cli init
```

This sets up:
- **Cursor Skills** (`.claude/skills/`) — use `@agent *command` in Cursor
- **Cursor Rules** (`.cursor/rules/`)
- **Configuration** (`.tapps-agents/config.yaml`)
- **Workflow presets** (`workflows/presets/`)

## 3. Try It in Cursor

In Cursor chat:

- `@reviewer *help`
- `@reviewer *score <file>`
- `@simple-mode *build "Add a small utility function"`
- `@simple-mode *review <file>`

## 4. Or Use the CLI

```bash
tapps-agents reviewer score path/to/file.py
tapps-agents doctor
tapps-agents workflow rapid --prompt "Add feature" --auto
```

## Next Steps

- **[Cursor Skills Installation Guide](../CURSOR_SKILLS_INSTALLATION_GUIDE.md)** — full setup and troubleshooting
- **[Simple Mode Guide](../SIMPLE_MODE_GUIDE.md)** — natural language workflows
- **[Configuration](../CONFIGURATION.md)** — config and experts
