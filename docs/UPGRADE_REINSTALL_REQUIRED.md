# Upgrade Reinstall Required - ModuleNotFoundError After Upgrade

## Problem

After upgrading to version 3.0.1 (or any new version), you may encounter:

```
ModuleNotFoundError: No module named 'tapps_agents.agents.analyst'
```

This error occurs when trying to run any CLI command that imports agent modules.

## Root Cause

When upgrading code to a new version but **not reinstalling the package**, editable installs can have **stale metadata** that prevents Python from finding modules correctly. This happens because:

1. You upgraded the code (e.g., `git pull` or `git checkout v3.0.1`)
2. The package version in the code changed (3.0.0 → 3.0.1)
3. But the editable install metadata still references the old version (3.0.0)
4. Python's import system gets confused and can't resolve module paths correctly

## Solution

**Important**: Make sure you're installing from the correct directory that has version 3.0.1!

**Reinstall the package** to refresh the editable install metadata:

```bash
# Navigate to TappsCodingAgents directory (the one with version 3.0.1)
cd /path/to/TappsCodingAgents

# Verify the version in the source code
cat pyproject.toml | grep "^version"
# Should show: version = "3.0.1"

# Reinstall in editable mode (refreshes metadata)
pip install -e .
```

**If you have multiple TappsCodingAgents directories**: Make sure you're installing from the directory that has `pyproject.toml` with `version = "3.0.1"`, not an older copy.

If you're using a regular (non-editable) installation:

```bash
# Upgrade to the new version
pip install --upgrade tapps-agents==3.0.1
```

## Verify the Fix

After reinstalling, verify the fix works:

```bash
# Check version (should show 3.0.1, not 3.0.0)
python -m tapps_agents.cli --version

# Verify it's importing from the correct location
python -c "import tapps_agents; print(f'Version: {tapps_agents.__version__}'); print(f'Location: {tapps_agents.__file__}')"

# Test that imports work
python -m tapps_agents.cli reviewer review --help

# Or test a specific agent command
python -m tapps_agents.cli analyst gather-requirements --help
```

**Note**: If the version still shows `3.0.0`, you may be installing from a directory that hasn't been updated. Check that:
1. The `pyproject.toml` in the directory you're installing from shows `version = "3.0.1"`
2. The `tapps_agents/__init__.py` shows `__version__ = "3.0.1"`
3. You're installing from the correct directory (not an old copy)

## Prevention

To avoid this issue in the future, **always reinstall after upgrading** when using editable installs:

```bash
# Standard upgrade workflow for editable installs:
cd /path/to/TappsCodingAgents
git pull origin main        # Get latest code
git checkout v3.0.1         # Or checkout specific version/tag
pip install -e .            # IMPORTANT: Reinstall to refresh metadata
```

## Related Issues

This is related to Python's editable install mechanism (`pip install -e .`). When package structure or version changes, the editable install metadata can become stale, requiring a reinstall to refresh it.

**Important**: If you have multiple TappsCodingAgents directories on your system, Python will import from the editable install location regardless of where you run commands. See [MULTIPLE_INSTALLATIONS_WARNING.md](MULTIPLE_INSTALLATIONS_WARNING.md) for details.

See also:
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting guide
- [TROUBLESHOOTING_UPGRADE.md](TROUBLESHOOTING_UPGRADE.md) - Detailed upgrade instructions
- [MULTIPLE_INSTALLATIONS_WARNING.md](MULTIPLE_INSTALLATIONS_WARNING.md) - Multiple installation directory conflicts

