# Installation Analysis - Source vs Installed Package

## Summary

**Status:** ✅ Safe (recommended: editable install)

When working in this repository, you typically want Python to import **the local source tree** (`./tapps_agents/`) rather than an older copy from `site-packages`.

## Recommended Setup (Development)

Use an isolated virtual environment and an editable install:

```powershell
python -m venv .venv
.venv\Scripts\activate

pip install -e .
python -c "import tapps_agents; print(tapps_agents.__version__)"
```

## Why this matters

- If you install a wheel normally (non-editable), Python may import the installed distribution instead of your current working copy.
- With an editable install, imports resolve to your working tree while still installing dependencies.

## How to verify which code is being used

```powershell
python -c "import tapps_agents, inspect; print(tapps_agents.__version__); print(inspect.getfile(tapps_agents))"
```

You should see a path under this repo (e.g., `...\TappsCodingAgents\tapps_agents\__init__.py`).

## Notes

- The package version is defined in `tapps_agents/__init__.py`.
- The distribution metadata and console script are defined in `pyproject.toml`.
