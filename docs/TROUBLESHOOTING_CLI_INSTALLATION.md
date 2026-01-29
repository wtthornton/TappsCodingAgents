# Troubleshooting: CLI Installation and PATH (Windows)

When you install `tapps-agents` with `pip install tapps-agents` (or `pip install tapps-agents==3.5.31`), the package installs correctly, but on **Windows** the `tapps-agents` command may not be found in the terminal.

## Why this happens

- **User install:** If pip installs to your user site-packages (e.g. `C:\Users\<you>\AppData\Roaming\Python\Python313\site-packages`), the `tapps-agents` executable is placed in the **user Scripts** folder (e.g. `C:\Users\<you>\AppData\Roaming\Python\Python313\Scripts`).
- **PATH:** On Windows, this user Scripts directory is often **not** on your PATH, so the shell cannot find `tapps-agents` even though the package is installed.

The installed version is correct (e.g. 3.5.31); the only issue is how the `tapps-agents` command is found (PATH or environment).

## Solutions (pick one)

### 1. Use the module (works everywhere)

Run the CLI via Python’s module interface. This works regardless of PATH:

```powershell
python -m tapps_agents.cli --version
python -m tapps_agents.cli init
python -m tapps_agents.cli doctor
```

Use this whenever `tapps-agents` is not found.

### 2. Use a project virtual environment (recommended)

Install and run inside a project venv so the executable is on that environment’s PATH:

```powershell
# Create and activate venv in your project
py -3.13 -m venv .venv
.venv\Scripts\activate

# Install from PyPI
pip install tapps-agents

# Or install a specific version from GitHub
pip install "tapps-agents @ git+https://github.com/wtthornton/TappsCodingAgents.git@v3.5.31"

tapps-agents --version
tapps-agents init
```

After activation, `tapps-agents` is available in that terminal.

### 3. Use the full path to the executable

Call the script by its full path (adjust Python version if needed):

```powershell
& "$env:APPDATA\Python\Python313\Scripts\tapps-agents.exe" --version
```

### 4. Add user Scripts to your PATH

Add the user Scripts directory to your user PATH so `tapps-agents` works in new terminals:

```powershell
$scripts = "$env:APPDATA\Python\Python313\Scripts"
if ($env:PATH -notlike "*$scripts*") {
  [Environment]::SetEnvironmentVariable("Path", $env:PATH + ";$scripts", "User")
}
```

Close and reopen the terminal, then run:

```powershell
tapps-agents --version
```

## Summary

| Situation | What to do |
|-----------|------------|
| `tapps-agents` not found | Use `python -m tapps_agents.cli` instead |
| Prefer a clean, project-scoped setup | Use a project `.venv` and `pip install tapps-agents` there |
| Want `tapps-agents` on PATH globally | Add user Scripts to PATH (option 4) or use full path (option 3) |

See also: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for other issues (config, Ruff/mypy, etc.).
