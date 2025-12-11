# Super Simple Upload

## Just 2 Steps:

### 1. Get Your Token
- **TestPyPI:** https://test.pypi.org/manage/account/token/
- **Production PyPI:** https://pypi.org/manage/account/token/

Copy the token (starts with `pypi-`)

### 2. Run This One Command

**For TestPyPI:**
```powershell
$env:TWINE_PASSWORD = "pypi-your-token-here"; python -m twine upload --repository testpypi dist/*
```

**For Production PyPI:**
```powershell
$env:TWINE_PASSWORD = "pypi-your-token-here"; python -m twine upload dist/*
```

Replace `pypi-your-token-here` with your actual token.

---

## Or Use the Script

```powershell
.\upload_to_pypi.ps1 -Token "pypi-your-token-here"
```

---

**That's it!** The warning about "trusted publishing" is normal and can be ignored.

