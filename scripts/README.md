# Scripts

Utility scripts for development, validation, and release.

## Structure

| Script | Purpose |
|--------|---------|
| **Release** | |
| `update_version.ps1` | Update version in pyproject.toml, `__init__.py`, docs/implementation/IMPROVEMENT_PLAN.json, docs |
| `create_github_release.ps1` | Create GitHub release from tag |
| `validate_release_readiness.ps1` | Pre-release validation |
| `verify_release_package.ps1` | Verify package artifacts |
| `upload_to_pypi.ps1` | Upload to PyPI |
| **Validation** | |
| `validate_*.py` | Various validation scripts (dependencies, docs, agent docs, etc.) |
| `verify_*.py` | Verification (docs, Cursor API, release package, Context7, path handling) |
| **Checks** (`checks/`) | |
| `check_*.py` | Runtime and environment checks (agents, DB, MCP, Context7, Windows) |
| **Maintenance** | |
| `analyze_project.py`, `analyze_and_fix.py` | Project analysis and improvement |
| `execute_improvements.py` | Run improvement plan |
| `prepopulate_context7_cache.py` | Pre-populate Context7 cache |
| `fix_context7_mcp.py` | Fix Context7 MCP configuration |
| **Testing** | |
| `run_*_tests*.py`, `run_*_tests.ps1` | Run unit, integration, e2e, doc tests |
| `run_tests_with_coverage.py` | Coverage runs |
| `quality_marathon.py` | Extended quality runs |

## Usage

- **Version bump**: `.\scripts\update_version.ps1 -Version 3.x.x`
- **Release**: see [Release Guide](../docs/operations/RELEASE_GUIDE.md)
- **Validate**: `python scripts/validate_dependencies.py`, `python scripts/verify_docs.py`, etc.
- **Checks**: `python scripts/checks/check_and_start_agents.py`, etc.
