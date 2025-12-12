# TappsCodingAgents

[![CI](https://github.com/wtthornton/TappsCodingAgents/actions/workflows/ci.yml/badge.svg)](https://github.com/wtthornton/TappsCodingAgents/actions/workflows/ci.yml)
[![Tests](https://github.com/wtthornton/TappsCodingAgents/actions/workflows/test.yml/badge.svg)](https://github.com/wtthornton/TappsCodingAgents/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-%E2%89%A53.13-blue)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/github/v/tag/wtthornton/TappsCodingAgents?label=version)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](pyproject.toml)

**A specification-first framework for defining, configuring, and orchestrating AI coding agents (plus a working reference implementation).**

> This repo both **develops** the TappsCodingAgents framework and **uses** it to build itself (“self-hosting”). See [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md).

<details>
<summary><strong>Table of contents</strong></summary>

- [What this is](#what-this-is)
- [Quick start](#quick-start)
- [Common commands](#common-commands)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Project status](#project-status)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

</details>

## What this is

TappsCodingAgents is a framework for building and running “coding agents” with a consistent interface and repeatable workflows:

- **Workflow agents (13)**: SDLC-focused agents (plan/design/implement/test/review/docs/ops/orchestrate).
- **Experts**: built-in technical experts + project-defined domain experts, with weighted consultation.
- **Workflow engine**: YAML-defined workflows and presets.
- **Model abstraction**: local-first (e.g., Ollama) with optional cloud fallback.
- **Cursor integration**: Cursor Skills + Background Agents support (see docs).

## Quick start

Full guide: [`QUICK_START.md`](QUICK_START.md)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

tapps-agents --help
tapps-agents doctor
```

## Common commands

More examples: [`QUICK_START.md`](QUICK_START.md) and [`docs/API.md`](docs/API.md)

```bash
# Review / score code
python -m tapps_agents.cli reviewer score path/to/file.py
python -m tapps_agents.cli reviewer review path/to/file.py

# Run workflow presets
python -m tapps_agents.cli workflow list
python -m tapps_agents.cli workflow rapid
python -m tapps_agents.cli workflow full

# Experts (optional)
python -m tapps_agents.cli setup-experts init
python -m tapps_agents.cli setup-experts add
```

## Configuration

Create `.tapps-agents/config.yaml` in the root of the project you want to operate on:

```bash
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

Schema and options: [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)

## Documentation

- **Start here**: [`docs/README.md`](docs/README.md)
- **Quick start**: [`QUICK_START.md`](QUICK_START.md)
- **API + CLI**: [`docs/API.md`](docs/API.md)
- **Architecture**: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Cursor Skills**: [`docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md`](docs/CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- **Background Agents**: [`docs/BACKGROUND_AGENTS_GUIDE.md`](docs/BACKGROUND_AGENTS_GUIDE.md)
- **Multi-agent orchestration**: [`docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md`](docs/MULTI_AGENT_ORCHESTRATION_GUIDE.md)

## Project status

- **Changelog**: [`CHANGELOG.md`](CHANGELOG.md)
- **Roadmap**: [`QUALITY_IMPROVEMENT_ROADMAP.md`](QUALITY_IMPROVEMENT_ROADMAP.md)
- **Progress tracking**: [`QUALITY_IMPROVEMENT_PROGRESS.md`](QUALITY_IMPROVEMENT_PROGRESS.md)
- **Implementation notes**: [`README_IMPLEMENTATION.md`](README_IMPLEMENTATION.md)

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

Local checks (matches CI):

```bash
ruff check .
ruff format --check .
python -m pytest -q
python -m mypy tapps_agents/core tapps_agents/workflow tapps_agents/context7
```

## Security

Please follow [`SECURITY.md`](SECURITY.md). For non-security bugs/features, open a GitHub issue.

## License

MIT (declared in [`pyproject.toml`](pyproject.toml)).  
