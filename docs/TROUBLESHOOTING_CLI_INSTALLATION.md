# Troubleshooting: CLI Command Not Found

## Problem

After installing `tapps-agents`, the `tapps-agents` command is not recognized:

```
tapps-agents : The term 'tapps-agents' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

## Root Cause

The console script entry point wasn't properly registered during installation. This can happen when:
1. Package installed in editable mode but entry points not re-registered
2. Virtual environment's Scripts directory not in PATH
3. Installation didn't complete properly
4. Windows-specific PATH issues

## Solutions

### Solution 1: Use Module Invocation (Immediate Workaround)

Instead of `tapps-agents`, use the Python module invocation:

```bash
# Instead of: tapps-agents init
python -m tapps_agents.cli init

# Instead of: tapps-agents reviewer review file.py
python -m tapps_agents.cli reviewer review file.py

# Instead of: tapps-agents workflow rapid
python -m tapps_agents.cli workflow rapid
```

**This works immediately** and doesn't require fixing the installation.

### Solution 2: Reinstall Package (Recommended)

Reinstall the package to ensure entry points are properly registered:

```bash
# Uninstall first
pip uninstall tapps-agents -y

# Reinstall in editable mode (if installing from source)
pip install -e .

# OR reinstall from PyPI (if published)
pip install tapps-agents
```

**For editable installs**, you may need to reinstall after making changes:

```bash
pip install -e . --force-reinstall --no-deps
```

### Solution 3: Verify Entry Point Installation

Check if the entry point script was created:

**Windows:**
```powershell
# Check if script exists
Test-Path .venv\Scripts\tapps-agents.exe
Test-Path .venv\Scripts\tapps-agents-script.py

# List all scripts
Get-ChildItem .venv\Scripts\tapps-agents*
```

**Linux/Mac:**
```bash
# Check if script exists
ls -la .venv/bin/tapps-agents

# Check entry points
pip show -f tapps-agents | grep -A 5 "Entry-points"
```

### Solution 4: Check PATH Configuration

Ensure your virtual environment's Scripts/bin directory is in PATH:

**Windows PowerShell:**
```powershell
# Check current PATH
$env:PATH -split ';' | Select-String "venv"

# Add to PATH for current session
$env:PATH += ";$PWD\.venv\Scripts"

# Verify
where.exe tapps-agents
```

**Windows CMD:**
```cmd
# Check PATH
echo %PATH%

# Add to PATH for current session
set PATH=%PATH%;%CD%\.venv\Scripts

# Verify
where tapps-agents
```

**Linux/Mac:**
```bash
# Check PATH
echo $PATH | tr ':' '\n' | grep venv

# Add to PATH for current session
export PATH="$PWD/.venv/bin:$PATH"

# Verify
which tapps-agents
```

### Solution 5: Manual Script Creation (Advanced)

If entry points still don't work, you can create a wrapper script:

**Windows (create `tapps-agents.bat` in Scripts directory):**
```batch
@echo off
python -m tapps_agents.cli %*
```

**Linux/Mac (create `tapps-agents` in bin directory):**
```bash
#!/bin/bash
python -m tapps_agents.cli "$@"
```

Make it executable (Linux/Mac):
```bash
chmod +x .venv/bin/tapps-agents
```

## Verification

After applying a solution, verify the CLI works:

```bash
# Test help command
python -m tapps_agents.cli --help

# OR if entry point works:
tapps-agents --help

# Test init command
python -m tapps_agents.cli init

# Test reviewer
python -m tapps_agents.cli reviewer --help
```

## Why This Happens

### Entry Point Configuration

The CLI is configured in two places:

1. **pyproject.toml:**
```toml
[project.scripts]
tapps-agents = "tapps_agents.cli:main"
```

2. **setup.py:**
```python
entry_points={
    "console_scripts": [
        "tapps-agents=tapps_agents.cli:main",
    ],
}
```

### Installation Process

When `pip install` runs:
1. It reads entry points from `pyproject.toml` or `setup.py`
2. Creates wrapper scripts in `venv/Scripts/` (Windows) or `venv/bin/` (Linux/Mac)
3. These scripts should be in PATH automatically

### Common Issues

1. **Editable installs**: Entry points may not update if package structure changes
2. **PATH not updated**: Virtual environment activation should add Scripts/bin to PATH
3. **Windows permissions**: Script creation may fail silently
4. **Multiple Python installations**: Wrong pip/Python used for installation

## Prevention

### Best Practices

1. **Always activate virtual environment:**
   ```bash
   # Windows
   .venv\Scripts\Activate.ps1
   
   # Linux/Mac
   source .venv/bin/activate
   ```

2. **Use module invocation in scripts:**
   ```python
   # More reliable than entry points
   subprocess.run(["python", "-m", "tapps_agents.cli", "init"])
   ```

3. **Verify installation:**
   ```bash
   pip show tapps-agents
   pip list | grep tapps-agents
   ```

4. **Check entry points after install:**
   ```bash
   pip show -f tapps-agents | grep Entry-points
   ```

## Related Documentation

- [Installation Guide](CURSOR_SKILLS_INSTALLATION_GUIDE.md)
- [CLI Documentation](API.md#cli)
- [Quick Start Guide](QUICK_START.md)

## Still Having Issues?

If none of these solutions work:

1. **Check Python version:** Requires Python 3.13+
   ```bash
   python --version
   ```

2. **Check package installation:**
   ```bash
   pip list | grep tapps-agents
   pip show tapps-agents
   ```

3. **Check CLI module exists:**
   ```bash
   python -c "import tapps_agents.cli; print(tapps_agents.cli.__file__)"
   ```

4. **Try fresh virtual environment:**
   ```bash
   python -m venv fresh_venv
   fresh_venv\Scripts\activate  # Windows
   pip install -e .
   python -m tapps_agents.cli --help
   ```

5. **Report issue:** Include:
   - Python version
   - Operating system
   - Installation method (pip install -e . or pip install tapps-agents)
   - Virtual environment type
   - Full error message

