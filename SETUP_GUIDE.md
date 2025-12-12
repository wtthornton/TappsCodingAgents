# TappsCodingAgents - Setup Guide

This guide helps you verify the repository (or your project) is set up correctly and highlights the most useful entrypoints.

---

## ✅ Verify Installation

From the repo root:

```bash
# Print installed package version
python -c "import tapps_agents; print(tapps_agents.__version__)"

# Show CLI help
python -m tapps_agents.cli --help

# List workflow presets
python -m tapps_agents.cli workflow list

# List configured experts (if any)
python -m tapps_agents.cli setup-experts list
```

---

## Optional: Local LLM (Ollama)

If you want local model execution:

```bash
ollama pull qwen2.5-coder:7b
ollama list
```

---

## Project Configuration (optional)

Create `.tapps-agents/config.yaml` in your project root.

```bash
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

See `docs/CONFIGURATION.md` for the schema.

---

## Common Commands

```bash
# Score / review
python -m tapps_agents.cli reviewer score example_bug.py
python -m tapps_agents.cli reviewer review example_bug.py

# Workflows
python -m tapps_agents.cli workflow rapid

# Experts
python -m tapps_agents.cli setup-experts init

# Analytics
python -m tapps_agents.cli analytics dashboard
```

---

## Notes

- The config loader searches upward for `.tapps-agents/config.yaml` and uses defaults if not found.
- The project profile file is `.tapps-agents/project-profile.yaml`.

---

**Framework Version**: 2.0.0
