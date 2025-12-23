# Installation Troubleshooting Guide

This guide addresses common installation issues with TappsCodingAgents.

## Common Issues

### 1. Dependency Conflict: `packaging` Version

**Error Message:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. 
This behaviour is the source of the following dependency conflicts.
langchain-core 0.2.43 requires packaging<25,>=23.2, but you have packaging 25.0 which is incompatible.
```

**Cause:**
- TappsCodingAgents doesn't directly depend on `langchain-core`, but another package in your environment does
- The latest `packaging` (25.0) was installed, but `langchain-core` requires `<25`

**Solution:**
1. **Reinstall with updated constraints** (recommended):
   ```bash
   pip install --upgrade --force-reinstall -e ".[dev]"
   ```

2. **Or manually constrain packaging**:
   ```bash
   pip install "packaging>=23.2,<25"
   ```

3. **If using a virtual environment** (recommended), create a fresh environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

**Status:** ✅ **Fixed in v2.4.1+** - `pyproject.toml` now includes `packaging>=23.2,<25` constraint

---

### 2. PATH Warning

**Warning Message:**
```
WARNING: The script tapps-agents is installed in 'C:\Users\...\AppData\Roaming\Python\Python313\Scripts' 
which is not on PATH.
Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
```

**Cause:**
- Scripts are installed to a location not in your system PATH
- This is common on Windows when using user-level Python installations

**Solution:**
1. **Add to PATH** (recommended for Windows):
   - Open System Properties → Environment Variables
   - Add `C:\Users\<YourUser>\AppData\Roaming\Python\Python313\Scripts` to PATH
   - Restart terminal/IDE

2. **Use module invocation** (no PATH changes needed):
   ```bash
   python -m tapps_agents.cli <command>
   ```

3. **Suppress warning** (not recommended):
   ```bash
   pip install --no-warn-script-location -e ".[dev]"
   ```

**Status:** ⚠️ **Non-blocking** - Package works, just use module invocation if PATH not configured

---

### 3. Version Mismatch

**Issue:**
- `pyproject.toml` shows version `2.3.0`
- Installed package shows version `2.4.0`

**Cause:**
- Package was installed in editable mode (`-e`)
- Version was updated in code but not in `pyproject.toml`

**Solution:**
1. **Update pyproject.toml** to match installed version (already fixed in v2.4.1+)
2. **Reinstall** to sync:
   ```bash
   pip install --upgrade -e ".[dev]"
   ```

**Status:** ✅ **Fixed in v2.4.1+** - Version now matches

---

### 4. Command Not Found: `tapps-agents`

**Error:**
```bash
tapps-agents: command not found
```

**Cause:**
- Script not in PATH (see Issue #2)
- Entry point not installed correctly

**Solution:**
1. **Use module invocation** (always works):
   ```bash
   python -m tapps_agents.cli <command>
   ```

2. **Check installation**:
   ```bash
   python -m pip show tapps-agents
   ```

3. **Reinstall**:
   ```bash
   pip install --force-reinstall -e ".[dev]"
   ```

**Status:** ⚠️ **Workaround available** - Use module invocation

---

### 5. Python Version Requirements

**Error:**
```
ERROR: Package 'tapps-agents' requires a different Python: 3.13.0 not in '>=3.13'
```

**Cause:**
- TappsCodingAgents requires Python 3.13+
- You're using an older Python version

**Solution:**
1. **Upgrade Python** to 3.13 or later:
   - Download from [python.org](https://www.python.org/downloads/)
   - Or use `pyenv` (Linux/Mac) or `pyenv-win` (Windows)

2. **Verify Python version**:
   ```bash
   python --version
   ```

**Status:** ✅ **Documented** - Python 3.13+ required (see `pyproject.toml`)

---

## Best Practices

### Use Virtual Environments

Always use a virtual environment to avoid dependency conflicts:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install
pip install -e ".[dev]"
```

### Use Module Invocation

If PATH issues occur, use module invocation:

```bash
# Instead of: tapps-agents init
python -m tapps_agents.cli init

# Instead of: tapps-agents reviewer review file.py
python -m tapps_agents.cli reviewer review file.py
```

### Check Installation

Verify installation:

```bash
# Check package info
python -m pip show tapps-agents

# Check entry point
python -m tapps_agents.cli --help
```

### Report Issues

If you encounter issues not covered here:

1. **Check existing issues**: [GitHub Issues](https://github.com/wtthornton/TappsCodingAgents/issues)
2. **Create new issue**: Include:
   - Python version: `python --version`
   - Installation method: `pip install -e ".[dev]"` or `pip install tapps-agents`
   - Full error message
   - Operating system
   - Virtual environment status

---

## Quick Reference

| Issue | Status | Solution |
|-------|--------|----------|
| `packaging` conflict | ✅ Fixed v2.4.1+ | Reinstall or use virtual environment |
| PATH warning | ⚠️ Non-blocking | Use module invocation or add to PATH |
| Version mismatch | ✅ Fixed v2.4.1+ | Already resolved |
| Command not found | ⚠️ Workaround | Use `python -m tapps_agents.cli` |
| Python version | ✅ Documented | Upgrade to Python 3.13+ |

---

## Related Documentation

- [Dependency Policy](DEPENDENCY_POLICY.md) - Full dependency management policy
- [Developer Guide](DEVELOPER_GUIDE.md) - Setup and development workflow
- [CLI Installation Fix](TROUBLESHOOTING_CLI_INSTALLATION.md) - CLI-specific troubleshooting

