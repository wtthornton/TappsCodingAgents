# Release Package Contents

This document specifies what files and folders are included or excluded in GitHub release packages for TappsCodingAgents.

## Purpose

Release packages should contain **only runtime files** needed for users to install and use `tapps-agents`. Development files, tests, documentation, and IDE-specific configurations are excluded to minimize package size and ensure clean installations.

## Files Included in Releases

### Core Package Files
- `tapps_agents/` - Main package directory containing all Python code
  - All agent implementations
  - CLI commands and parsers
  - Core framework code
  - Expert system
  - Workflow engine
  - Context7 integration
  - MCP gateway
  - Health checks
  - Quality tools
  - **Resources directory** (`tapps_agents/resources/`) - Required runtime resources:
    - Cursor Skills definitions (`.claude/skills/`)
    - Cursor Rules (`.cursor/rules/`)
    - Workflow presets (`.workflows/presets/`)
    - Customization examples

### Package Metadata
- `pyproject.toml` - Package metadata, dependencies, and build configuration
- `setup.py` - Setup script (minimal stub, metadata in pyproject.toml)
- `MANIFEST.in` - Package data inclusion rules
- `README.md` - User documentation and quick start guide
- `LICENSE` - MIT License file
- `requirements.txt` - Runtime dependencies (if present)

## Files Excluded from Releases

### Development Files
- `tests/` - All test files and test fixtures
- `examples/` - Example code and demonstration files
- `scripts/` - Development and utility scripts
- `workflows/` - Workflow definition files (not needed for runtime)
- `requirements/` - Requirements documentation and templates
- `templates/` - Project templates (not needed for runtime)
- `implementation/` - Implementation documentation and plans
- `docs/` - All documentation (available on GitHub)

### IDE and Tool Configurations
- `.claude/` - Claude IDE configuration (not needed in package)
- `.cursor/` - Cursor IDE configuration (not needed in package)
- `.bmad-core/` - BMAD framework configuration
- `.ruff_cache/` - Ruff linter cache
- `.pytest_cache/` - Pytest cache
- `.mypy_cache/` - MyPy type checker cache

### Test Projects
- `billstest/` - Test project directory

### Build Artifacts
- `dist/` - Distribution packages (built during release)
- `build/` - Build artifacts
- `*.egg-info/` - Egg metadata directories
- `htmlcov/` - HTML coverage reports
- `reports/` - Quality and analysis reports
- `coverage.json` - Coverage data
- `test-results.xml` - Test result files
- `MagicMock/` - Mock object artifacts

### Other Exclusions
- `__pycache__/` - Python bytecode cache
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files
- `.venv/`, `venv/`, `ENV/` - Virtual environments
- `.git/` - Git repository data
- `.DS_Store`, `Thumbs.db` - OS-specific files

## Version Update Locations

When creating a release, the version number must be updated in:

1. **`pyproject.toml`** - Line 7: `version = "X.Y.Z"`
2. **`tapps_agents/__init__.py`** - Line 5: `__version__ = "X.Y.Z"`

Both locations must be updated atomically to maintain consistency.

## Build Process

The release build process:

1. Updates version numbers in both locations
2. Cleans previous build artifacts (`dist/`, `build/`, `*.egg-info/`)
3. Builds distribution packages using `python -m build`:
   - Source distribution (`.tar.gz`)
   - Wheel distribution (`.whl`)
4. Verifies package contents contain only runtime files
5. Creates GitHub release with built packages attached

## Package Verification

Before creating a release, verify that built packages:

- ✅ Contain only files listed in "Files Included" section
- ✅ Do not contain any files listed in "Files Excluded" section
- ✅ Can be installed successfully: `pip install tapps-agents-X.Y.Z.whl`
- ✅ CLI works after installation: `tapps-agents --version`
- ✅ All agents are accessible: `tapps-agents reviewer --help`

## MANIFEST.in Rules

The `MANIFEST.in` file controls what gets included in source distributions. Current rules:

- **Include**: `tapps_agents/resources/*` (recursive)
- **Exclude**: All development directories, test files, IDE configs, build artifacts

See `MANIFEST.in` for the complete exclusion list.

## Notes

- Documentation is available on GitHub, so it doesn't need to be in the package
- Users can access full documentation via the repository
- The package focuses on runtime functionality only
- Development tools and test files are not needed for end users

