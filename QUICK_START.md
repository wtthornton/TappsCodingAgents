# TappsCodingAgents - Quick Start Guide

**Get up and running in ~10 minutes**

---

## Prerequisites

- **Python 3.13+** (recommended: latest stable Python)
- (Optional, for local LLM) **Ollama**

---

## Installation

From this repository root:

```bash
# Create and activate a venv (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# Install
pip install -e .
```

This installs the `tapps-agents` console script and the `tapps_agents` Python package.

---

## Verify CLI

```bash
tapps-agents --help

# (Alternative)
python -m tapps_agents.cli --help
```

---

## Initialize Your Project (recommended)

Run the initializer to install **Cursor Rules**, **workflow presets**, **Cursor Skills**, **Background Agents config**, **.cursorignore**, and a starter `.tapps-agents/config.yaml`:

**What gets installed:**
- **`.cursor/rules/`**: Cursor Rules (.mdc files) - AI context documentation
- **`.claude/skills/`**: Cursor Skills - Agent capabilities for Cursor's Skills system
- **`.cursor/background-agents.yaml`**: Background Agents configuration
- **`.cursorignore`**: Indexing optimization (excludes large/generated files)
- **`workflows/presets/`**: Workflow preset definitions
- **`.tapps-agents/config.yaml`**: Framework configuration

```bash
tapps-agents init

# (Alternative)
python -m tapps_agents.cli init
```

This is the easiest way to ensure your project is fully set up to leverage TappsCodingAgents.

## Check Your Environment (recommended)

Run `doctor` to validate your local environment and toolchain. It **soft-degrades with warnings** by default.

```bash
tapps-agents doctor

# (Alternative + JSON output)
python -m tapps_agents.cli doctor --format json
```

---

## Optional: Install Ollama + Pull a Model

If you want local LLM execution:

```bash
# Pull a coding model
ollama pull qwen2.5-coder:7b

# Verify
ollama list
```

### Note (Cursor-first policy)

When running inside **Cursor** (Skills / Background Agents), Cursor uses the developer’s configured model.
The framework’s MAL (including Ollama) is intended for **headless usage** only.

If you explicitly want to enable MAL while running the CLI from a Cursor-launched shell, run with:

```bash
# Enable MAL for this process (optional)
export TAPPS_AGENTS_MODE=headless
```

### Windows PowerShell equivalent

```powershell
$env:TAPPS_AGENTS_MODE = "headless"
```

---

## Common Commands

### Review / score code

```bash
# Fast scoring (no LLM feedback)
python -m tapps_agents.cli reviewer score path/to/file.py

# Full review (uses LLM feedback when available)
python -m tapps_agents.cli reviewer review path/to/file.py

# Phase 6 tools
python -m tapps_agents.cli reviewer lint path/to/file.py
python -m tapps_agents.cli reviewer type-check path/to/file.py
python -m tapps_agents.cli reviewer report path/to/dir json markdown html
python -m tapps_agents.cli reviewer duplication path/to/dir
python -m tapps_agents.cli reviewer analyze-project

# Quick shortcut (same as reviewer score)
python -m tapps_agents.cli score path/to/file.py
```

### Generate / refactor code

```bash
python -m tapps_agents.cli implementer implement "Create a function to calculate factorial" factorial.py
python -m tapps_agents.cli implementer refactor path/to/file.py "Extract helper functions"
```

### Generate tests

```bash
python -m tapps_agents.cli tester test path/to/file.py
python -m tapps_agents.cli tester run-tests
```

### Run workflow presets

```bash
python -m tapps_agents.cli workflow list
python -m tapps_agents.cli workflow rapid
python -m tapps_agents.cli workflow full
python -m tapps_agents.cli workflow fix
python -m tapps_agents.cli workflow quality
python -m tapps_agents.cli workflow hotfix
```

### Set up experts (optional)

```bash
python -m tapps_agents.cli setup-experts init
python -m tapps_agents.cli setup-experts add
python -m tapps_agents.cli setup-experts list
```

### Analytics (optional)

```bash
python -m tapps_agents.cli analytics dashboard
python -m tapps_agents.cli analytics system
```

### Create new project (primary use case)

```bash
# Create a complete project from description
python -m tapps_agents.cli create "Build a task management web app"
python -m tapps_agents.cli create "Create a REST API" --workflow rapid
```

### Hardware profile (optional)

```bash
# Check current hardware profile
python -m tapps_agents.cli hardware-profile

# Set hardware profile (for NUC/low-power systems)
python -m tapps_agents.cli hardware-profile --set nuc
```

---

## Configuration (optional)

Create `.tapps-agents/config.yaml` in your project root.

Start from the default template:

```bash
# Recommended: `tapps-agents init` (creates `.tapps-agents/config.yaml` for you)

# If you want to copy the template manually (macOS/Linux):
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

```powershell
# If you want to copy the template manually (Windows PowerShell):
New-Item -ItemType Directory -Force .tapps-agents | Out-Null
Copy-Item -Force templates\default_config.yaml .tapps-agents\config.yaml
```

Then see `docs/CONFIGURATION.md` for the full schema.

---

## Next Steps

- `docs/API.md`
- `docs/CONFIGURATION.md`
- `docs/WORKFLOW_SELECTION_GUIDE.md`
- `docs/EXPERT_SETUP_WIZARD.md`
