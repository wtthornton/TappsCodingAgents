# Twine Upload - Quick Reference (First 10 Lines)

```
usage: twine upload [-h] [-r REPOSITORY] [--repository-url REPOSITORY_URL]
                    [--attestations] [-s] [--sign-with SIGN_WITH]
                    [-i IDENTITY] [-u USERNAME] [-p PASSWORD]
                    [--non-interactive] [-c COMMENT]
                    [--config-file CONFIG_FILE] [--skip-existing]
                    [--cert path] [--client-cert path] [--verbose]
                    [--disable-progress-bar]
                    dist [dist ...]
```

## Full Help Output

The complete help text has been saved to `twine-upload-help.txt` in your project root.

## Workaround for Cursor AI Interception

**Problem:** When running `python -m twine upload --help | Select-Object -First 10` through Cursor's AI interface, you get a Request ID instead of output.

**Solution:** The help text is now available in:
- `twine-upload-help.txt` - Full help output
- This file - Quick reference

## Quick Commands

### View First 10 Lines (from saved file)
```powershell
Get-Content twine-upload-help.txt | Select-Object -First 10
```

### View Full Help
```powershell
Get-Content twine-upload-help.txt
```

### Or use standard terminal (outside Cursor AI)
Open a regular PowerShell window and run:
```powershell
python -m twine upload --help | Select-Object -First 10
```

