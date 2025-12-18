# Tech Stack (Lean BMAD Shard)

## Runtime

- **Language**: Python (requires `>=3.13`; see `pyproject.toml`)
- **CLI entrypoint**: `tapps-agents` (see `[project.scripts]` in `pyproject.toml`)

## Core Dependencies (selected)

- **Config & models**: `pydantic`
- **HTTP**: `httpx`, `aiohttp`
- **YAML**: `pyyaml`
- **System**: `psutil`
- **Analysis & reporting** (used by reviewer/reporting): `radon`, `bandit`, `coverage`, `jinja2`, `plotly`

## Dev Tooling (optional extras)

- **Formatting**: `black`
- **Linting**: `ruff`
- **Type checking**: `mypy`
- **Testing**: `pytest`, `pytest-asyncio`, `pytest-xdist`, `pytest-cov`, `pytest-timeout`

## Repo Docs

- `docs/DEVELOPER_GUIDE.md`
- `docs/DEPENDENCY_POLICY.md`
- `docs/ARCHITECTURE.md`


