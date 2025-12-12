# PyPI Upload Guide - Authentication Setup

## Understanding the Messages

### "This environment is not supported for trusted publishing"
**This is a WARNING, not an error.** It means:
- You're not in a CI/CD environment (like GitHub Actions)
- You need to use an API token instead of trusted publishing
- This is the normal way to upload from your local machine

### "Enter your API token:"
This is the authentication prompt. You need a PyPI API token to upload packages.

## Step 1: Get Your PyPI API Token

1. **Go to PyPI:** https://pypi.org/
2. **Log in** to your account
3. **Go to Account Settings:**
   - Click your username (top right)
   - Select "Account settings"
4. **Create API Token:**
   - Scroll to "API tokens" section
   - Click "Add API token"
   - Give it a name (e.g., "TappsCodingAgents Upload")
   - Set scope to "Entire account" (or just the project if you prefer)
   - Click "Add token"
5. **Copy the token immediately** - You'll only see it once!
   - Format: `pypi-...` (long string)

## Step 2: Upload Your Package

### Option A: Interactive (Enter token when prompted)
```powershell
python -m twine upload dist/*
# When prompted, paste your API token
```

### Option B: Use Environment Variable (Recommended)
Set the token as an environment variable:

**PowerShell (Current Session):**
```powershell
$env:TWINE_PASSWORD = "pypi-your-token-here"
python -m twine upload dist/*
```

**PowerShell (Permanent - User Level):**
```powershell
[System.Environment]::SetEnvironmentVariable('TWINE_PASSWORD', 'pypi-your-token-here', 'User')
```

**PowerShell (Permanent - System Level - Requires Admin):**
```powershell
[System.Environment]::SetEnvironmentVariable('TWINE_PASSWORD', 'pypi-your-token-here', 'Machine')
```

### Option C: Use .pypirc File (Alternative)
Create `%USERPROFILE%\.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-your-token-here
```

Then upload:
```powershell
python -m twine upload dist/*
```

## Step 3: Upload to TestPyPI First (Recommended)

Before uploading to production PyPI, test with TestPyPI:

1. **Get TestPyPI token:** https://test.pypi.org/manage/account/token/
2. **Upload to TestPyPI:**
```powershell
python -m twine upload --repository testpypi dist/*
```

3. **Test installation:**
```powershell
pip install -i https://test.pypi.org/simple/ tapps-agents
```

## Step 4: Upload to Production PyPI

Once tested, upload to production:

```powershell
python -m twine upload dist/*
```

## Security Best Practices

1. **Never commit tokens to git** - Add to `.gitignore`:
   ```
   .pypirc
   *.env
   ```

2. **Use environment variables** instead of command-line flags

3. **Use project-scoped tokens** when possible (instead of account-wide)

4. **Rotate tokens regularly**

5. **Use TestPyPI first** to verify everything works

## Troubleshooting

### "Invalid credentials"
- Check that your token starts with `pypi-`
- Ensure no extra spaces when copying
- Token might have expired - create a new one

### "File already exists"
- Use `--skip-existing` to skip files that are already uploaded:
  ```powershell
  python -m twine upload --skip-existing dist/*
  ```

### "403 Forbidden"
- Check token permissions
- Ensure token hasn't been revoked
- Verify you're using the correct repository (pypi vs testpypi)

## Quick Reference

```powershell
# Set token for current session
$env:TWINE_PASSWORD = "pypi-your-token-here"

# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*

# Upload with verbose output
python -m twine upload --verbose dist/*

# Upload and skip existing files
python -m twine upload --skip-existing dist/*
```

## Your Current Package

You have these files ready to upload (version will vary):
- `tapps_agents-<version>-py3-none-any.whl`
- `tapps_agents-<version>.tar.gz`

Both will be uploaded when you run the command.

