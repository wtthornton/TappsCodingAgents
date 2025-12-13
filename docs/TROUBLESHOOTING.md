# Troubleshooting Guide

**Version**: 2.0.0  
**Last Updated**: December 2025

## Installation

### `pip install` fails

- Ensure Python 3.13+ (recommended: latest stable Python):

```bash
python --version
```

- Upgrade tooling:

```bash
python -m pip install --upgrade pip
```

## CLI

### CLI runs but prints "Playwright not available"

Some browser-related functionality can run in a mocked mode if the **Python Playwright package** is not installed.

- If you're using **Cursor** with **Playwright MCP**, you can ignore this: browser automation should be done via Cursor Skills/Background Agents.
- If you need browser automation from the **CLI** (outside Cursor), install Playwright:

```bash
python -m pip install playwright
python -m playwright install
```

### "pytest is not recognized"

Some environments don’t expose `pytest` as a command. Use:

```bash
python -m pytest -q
```

(And ensure you installed dependencies in your venv.)

## Configuration

### "Configuration file not found"

This is not an error: configuration is optional.

If you want configuration, create:

- `.tapps-agents/config.yaml`

Recommended:

```bash
python -m tapps_agents.cli init
```

Or start from the template:

```bash
mkdir -p .tapps-agents
cp templates/default_config.yaml .tapps-agents/config.yaml
```

See `docs/CONFIGURATION.md`.

### Scoring weights validation error

If you see an error about weights not summing to 1.0, ensure `scoring.weights.*` totals ~1.0.

## Ollama / Local LLM

### Cannot connect to Ollama

- Verify Ollama is installed and running:

```bash
ollama list
```

- Ensure the URL in `.tapps-agents/config.yaml` matches your setup:

```yaml
mal:
  ollama_url: "http://localhost:11434"
```

### MAL disabled while running inside Cursor

If you see errors like **`MALDisabledInCursorModeError`**, that is expected when running the framework under Cursor
(including Cursor Background Agents). In this setup, **Cursor is the only LLM runtime** and the framework runs tools-only.

If you explicitly want to enable MAL for a headless CLI run, set:

```bash
export TAPPS_AGENTS_MODE=headless
```

## Quality Tools

### Ruff / mypy not found

These are Python dependencies. If you installed via `pip install -e .`, they should be available in the venv. Verify:

```bash
python -c "import ruff, mypy"  # may fail if not installed
```

Or run the CLI commands and inspect the error output:

```bash
python -m tapps_agents.cli reviewer lint path/to/file.py
python -m tapps_agents.cli reviewer type-check path/to/file.py
```

## Getting Help

- Run `python -m tapps_agents.cli --help`
- Check configuration docs: `docs/CONFIGURATION.md`
- File an issue with:
  - OS + Python version
  - CLI command you ran
  - full stack trace / output
