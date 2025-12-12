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

---

## Configuration (optional)

Create `.tapps-agents/config.yaml` in your project root.

Start from the default template:

```bash
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

Then see `docs/CONFIGURATION.md` for the full schema.

---

## Next Steps

- `docs/API.md`
- `docs/CONFIGURATION.md`
- `docs/WORKFLOW_SELECTION_GUIDE.md`
- `docs/EXPERT_SETUP_WIZARD.md`
