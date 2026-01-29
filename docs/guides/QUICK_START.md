---
title: Quick Start Guide
version: 3.5.30
status: active
last_updated: 2026-01-20
tags: [quick-start, getting-started, setup]
---

# Quick Start Guide

Get up and running with TappsCodingAgents in about 5–10 minutes.

## 1. Install

Requires **Python 3.13+** (`python --version`).

**For consuming projects (recommended):**
```bash
# Install from PyPI (clean install, framework code only)
pip install tapps-agents
# or specific version:
pip install tapps-agents==3.5.30
```

**For framework development (contributors):**
```bash
# Clone repository and install in editable mode
git clone https://github.com/wtthornton/TappsCodingAgents.git
cd TappsCodingAgents
python3.13 -m pip install -e .
# Windows: py -3.13 -m pip install -e .
```

After installing: `tapps-agents doctor` or `python -m tapps_agents.cli doctor` to verify.

### Windows

On Windows, a user-level `pip install` often puts the `tapps-agents` script in a Scripts folder that is not on PATH. Use a project venv (recommended) or `python -m tapps_agents.cli`; see [Troubleshooting CLI installation](../TROUBLESHOOTING_CLI_INSTALLATION.md).

```powershell
py -3.13 --version
# Recommended: use a project venv so tapps-agents is on PATH
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install tapps-agents
tapps-agents init

# Or without venv (use module if command not found):
# pip install tapps-agents
py -3.13 -m tapps_agents.cli init
```

### Linux/macOS

```bash
python3.13 --version
# For consuming projects:
pip install tapps-agents
# For development:
# git clone https://github.com/wtthornton/TappsCodingAgents.git
# cd TappsCodingAgents
# python3.13 -m pip install -e .
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
