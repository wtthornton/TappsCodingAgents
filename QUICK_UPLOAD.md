# Quick Upload Guide

## Easiest Way: Use the Upload Script

I've created an automated script that handles everything for you!

### Step 1: Get Your API Token

**For TestPyPI (recommended first):**
1. Go to: https://test.pypi.org/manage/account/token/
2. Create account if needed
3. Click "Add API token"
4. Copy the token (starts with `pypi-`)

**For Production PyPI:**
1. Go to: https://pypi.org/manage/account/token/
2. Create account if needed  
3. Click "Add API token"
4. Copy the token (starts with `pypi-`)

### Step 2: Run the Script

**Upload to TestPyPI (recommended first):**
```powershell
.\upload_to_pypi.ps1
```
The script will prompt you for your token.

**Or provide token directly:**
```powershell
.\upload_to_pypi.ps1 -Token "pypi-your-token-here"
```

**Upload to Production PyPI:**
```powershell
.\upload_to_pypi.ps1 -Repository pypi
```

**With options:**
```powershell
# Skip files that already exist
.\upload_to_pypi.ps1 -SkipExisting

# Verbose output
.\upload_to_pypi.ps1 -ShowVerbose

# Both
.\upload_to_pypi.ps1 -SkipExisting -ShowVerbose
```

## Alternative: Set Token Once, Use Anytime

Set your token as an environment variable, then just run twine:

```powershell
# Set token (current session only)
$env:TWINE_PASSWORD = "pypi-your-token-here"

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

## What the Script Does

1. ✅ Checks if dist/ folder exists
2. ✅ Lists files to be uploaded
3. ✅ Prompts for token if not provided
4. ✅ Validates token format
5. ✅ Runs the upload command
6. ✅ Cleans up (removes token from environment)
7. ✅ Shows success/failure status

## Security Note

The script automatically clears the token from the environment after use for security.

