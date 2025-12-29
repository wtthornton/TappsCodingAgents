# Troubleshooting: Upgrading TappsCodingAgents When CLI is Broken

## Problem

If you encounter this error when trying to use TappsCodingAgents:

```
ImportError: cannot import name '_version_' from 'tapps_agents' (unknown location)
```

This means you have an older version installed that has a bug preventing the CLI from running. You need to upgrade, but the CLI is broken so you can't use it to upgrade.

## Solution: Direct pip Upgrade

Upgrade directly using `pip`, bypassing the broken CLI:

### If installed via pip:

```bash
# Upgrade to latest version
pip install --upgrade tapps-agents

# Or upgrade to specific version
pip install --upgrade tapps-agents==3.0.1
```

### If installed in editable mode (development):

```bash
# Navigate to TappsCodingAgents directory
cd /path/to/TappsCodingAgents

# Pull latest changes
git pull origin main

# If upgrading to a specific version/tag
git checkout v3.0.1  # or latest tag

# IMPORTANT: Reinstall in editable mode to refresh metadata
# This fixes ModuleNotFoundError issues after upgrade
pip install -e .
```

**Why reinstall?** After upgrading code, the editable install metadata can become stale, causing `ModuleNotFoundError` for agent modules (e.g., `tapps_agents.agents.analyst`). Reinstalling refreshes the installation and resolves these import errors.

### If installed as git submodule:

```bash
# Navigate to the submodule directory
cd TappsCodingAgents

# Pull latest changes
git pull origin main

# If you need to update to a specific tag/version
git checkout v3.0.1

# Reinstall in editable mode (if needed)
pip install -e .
```

## Verify Upgrade

After upgrading, verify the installation:

```bash
# Check version (should work now)
python -m tapps_agents.cli --version

# Or check via Python
python -c "from tapps_agents import __version__; print(__version__)"
```

## What Was Fixed in 3.0.1

- **Fixed version import issues** - Added defensive import pattern with fallbacks
- **Added `_version_` alias** - For compatibility with different import mechanisms
- **Enhanced error handling** - Better handling of import failures in editable installs

## Prevention

To avoid this issue in the future:
- Keep TappsCodingAgents updated regularly
- Use `pip install --upgrade tapps-agents` periodically
- If using git submodule, pull updates regularly

