# Quick Fix: CLI Command Not Found

## The Problem

After installing `tapps-agents`, you tried to run:
```bash
tapps-agents init
```

But got this error:
```
tapps-agents : The term 'tapps-agents' is not recognized...
```

## Immediate Solution (Works Right Now)

**Use the Python module invocation instead:**

```bash
# Instead of: tapps-agents init
python -m tapps_agents.cli init

# Instead of: tapps-agents reviewer review file.py
python -m tapps_agents.cli reviewer review file.py

# Instead of: tapps-agents workflow rapid
python -m tapps_agents.cli workflow rapid
```

**This works immediately** - no need to fix the installation!

## Why This Happens

The `tapps-agents` command is a console script entry point that should be created during installation. On Windows, especially with editable installs, this sometimes doesn't work properly.

## Permanent Fix (Optional)

If you want the `tapps-agents` command to work, try:

1. **Reinstall the package:**
   ```bash
   pip uninstall tapps-agents -y
   pip install -e .
   ```

2. **Verify the script was created:**
   ```powershell
   # Windows PowerShell
   Test-Path .venv\Scripts\tapps-agents.exe
   ```

3. **If still not working, use module invocation** (it's just as good!)

## All Commands Work the Same Way

Both methods are equivalent:

| Entry Point | Module Invocation |
|------------|-------------------|
| `tapps-agents init` | `python -m tapps_agents.cli init` |
| `tapps-agents reviewer review file.py` | `python -m tapps_agents.cli reviewer review file.py` |
| `tapps-agents workflow rapid` | `python -m tapps_agents.cli workflow rapid` |
| `tapps-agents --help` | `python -m tapps_agents.cli --help` |

## Next Steps

1. **Use module invocation** for now: `python -m tapps_agents.cli init`
2. **Continue with your project** - everything else works the same
3. **Optional:** Try reinstalling later if you prefer the shorter command

For more details, see [Troubleshooting Guide](docs/TROUBLESHOOTING_CLI_INSTALLATION.md).

