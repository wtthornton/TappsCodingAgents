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

```bash
pip install -e .
```

Or from PyPI: `pip install tapps-agents`

## 2. Initialize Cursor Integration

```bash
# If 'tapps-agents' is not on PATH:
python -m tapps_agents.cli init

# Or:
tapps-agents init
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
