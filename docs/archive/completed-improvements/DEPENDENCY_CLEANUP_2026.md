# Dependency Cleanup 2026

**Date:** 2026-01-30
**Status:** Completed
**Summary:** Reduced dependency footprint by making Plotly optional, removing Black (Ruff handles formatting), and removing unused pylint.

## Changes Made

### 1. Plotly → Optional `[reporting]` Extra

- **Before:** Plotly was a core runtime dependency (~20+ transitive packages)
- **After:** Plotly moved to optional extra `[reporting]`
- **Rationale:** `HAS_PLOTLY` was defined in report_generator but never used. Report generator uses Jinja2 and ASCII charts by default.
- **Usage:** `pip install -e ".[reporting]"` for interactive trend charts (when implemented)

### 2. Black Removed (Ruff Replaces)

- **Before:** Black and Ruff both in dev deps; CI ran Ruff for lint and format
- **After:** Ruff only—handles both linting and formatting
- **Rationale:** CI already used `ruff format --check`; Black was redundant
- **Impact:** Simpler toolchain, 50–150x faster formatting with Ruff

### 3. Pylint Removed

- **Before:** Pylint in dev deps "for maintainability scoring"
- **After:** Removed from dev deps
- **Rationale:** Scoring uses Ruff and radon; no pylint subprocess calls anywhere

### 4. Doctor Command Updates

- Removed Black from `tool_cmds` and `python_tools` in `tapps_agents/core/doctor.py`
- Doctor no longer reports "Tool not found: black" as a warning

## Optional Extras Summary

| Extra | Purpose | Install |
|-------|---------|---------|
| `dev` | Development (ruff, mypy, pytest, etc.) | `pip install -e ".[dev]"` |
| `reporting` | Interactive charts (plotly) | `pip install -e ".[reporting]"` |
| `dependency-analysis` | pipdeptree (see DEPENDENCY_CONFLICT_PIPDEPTREE.md) | `pip install -e ".[dependency-analysis]"` |

## Files Modified

### Dependencies & Config
- `pyproject.toml` – Deps, optional extras, removed `[tool.black]`
- `requirements.txt` – Mirrored changes
- `tapps_agents/core/doctor.py` – Removed Black from tool checks
- `requirements/TECH_STACK.md` – Updated development tools table

### Expert Knowledge (RAG / Code Quality)
- `tapps_agents/experts/knowledge/code-quality-analysis/static-analysis-patterns.md` – Ruff replaces Black/pylint; updated pre-commit and CI examples
- `tapps_agents/experts/knowledge/code-quality-analysis/quality-gates.md` – Ruff pre-commit and CI examples (replaced Black + flake8)
- `tapps_agents/experts/knowledge/development-workflow/ci-cd-patterns.md` – Added Ruff lint/format steps to CI example

### Code
- `tapps_agents/agents/reviewer/report_generator.py` – Removed unused `HAS_PLOTLY` and `find_spec` import

## Not Changed (Deferred)

- **aiohttp:** Kept; may be used by MCP/Context7 integrations
- **packaging constraint:** Kept for langchain-core compatibility
- **aiofiles:** Kept; used by AsyncFileOps with sync fallback

## Verification

Run after upgrade:

```bash
# Validate dependency consistency
python scripts/validate_dependencies.py

# Doctor (should not report black as missing)
tapps-agents doctor

# CI passes (uses Ruff for format)
ruff format --check .
ruff check .
```
