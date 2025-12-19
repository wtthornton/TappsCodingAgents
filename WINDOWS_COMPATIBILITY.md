# Windows Compatibility Guide

## Overview

This document outlines Windows-specific compatibility considerations and fixes for TappsCodingAgents workflow execution.

## Issues Found and Fixed

### 1. Unicode Encoding Errors ✅ FIXED

**Problem:** Windows console (cp1252 encoding) cannot display Unicode characters like emojis (🚀, ✅, ❌) and special characters (█, ░) used in progress bars.

**Error:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680' in position 5
```

**Fix Applied:**
- Updated `tapps_agents/workflow/cursor_chat.py` to catch `UnicodeEncodeError` and fallback to ASCII-safe encoding
- Added UTF-8 encoding setup in `run_amazon_workflow.py` script

**Location:** `tapps_agents/workflow/cursor_chat.py:43-48`

### 1.1. Subprocess Unicode Decoding Errors ✅ FIXED (v2.0.6+)

**Problem:** When running quality analysis or report generation on Windows, subprocess calls would fail with:
```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 3626: character maps to <undefined>
```

This occurred because `subprocess.run()` with `text=True` defaults to system encoding (cp1252 on Windows), which cannot decode certain bytes in tool output.

**Fix Applied:**
- Added `encoding="utf-8"` and `errors="replace"` to all `subprocess.run()` calls with `text=True`
- Fixed 6 instances in `tapps_agents/agents/reviewer/scoring.py`:
  - 2 Ruff linting calls
  - 2 mypy type checking calls
  - 2 jscpd duplication detection calls
- Fixed 4 instances in `tapps_agents/agents/reviewer/typescript_scorer.py`:
  - 2 ESLint calls
  - 2 TypeScript compiler calls

**Location:** 
- `tapps_agents/agents/reviewer/scoring.py` (lines 589, 675, 722, 784, 894, 1022)
- `tapps_agents/agents/reviewer/typescript_scorer.py` (lines 235, 312, 448, 496)

**Impact:** Quality report generation and all code analysis tools now work correctly on Windows without encoding errors.

### 2. Console Encoding Setup ✅ FIXED

**Problem:** Python defaults to system encoding (cp1252 on Windows) which doesn't support full Unicode.

**Fix Applied:**
- Set `PYTHONIOENCODING=utf-8` environment variable
- Reconfigure stdout/stderr to UTF-8 encoding (Python 3.7+)

**Location:** `run_amazon_workflow.py:8-16`

## Windows-Specific Checks

### Run Compatibility Check

```powershell
cd TappsCodingAgents
python windows_compatibility_check.py
```

This will verify:
- ✅ Console encoding configuration
- ✅ Unicode character printing
- ✅ Path handling with Unicode characters
- ✅ Environment variable setup

## Running Workflows on Windows

### Method 1: Using the Helper Script (Recommended)

```powershell
cd TappsCodingAgents
python run_amazon_workflow.py
```

The script automatically:
- Sets UTF-8 encoding
- Configures environment variables
- Handles encoding errors gracefully

### Method 2: Using CLI with Environment Variable

```powershell
$env:PYTHONIOENCODING='utf-8'
cd TappsCodingAgents
python -m tapps_agents.cli workflow full --prompt "Your prompt here" --auto
```

### Method 3: Set Encoding Permanently (Optional)

Add to your PowerShell profile (`$PROFILE`):
```powershell
$env:PYTHONIOENCODING = "utf-8"
```

Or set system-wide environment variable:
1. Open System Properties → Environment Variables
2. Add `PYTHONIOENCODING` = `utf-8`

## Files Modified for Windows Compatibility

1. **`tapps_agents/workflow/cursor_chat.py`**
   - Added Unicode error handling in `send_update()` method
   - Gracefully falls back to ASCII-safe encoding

2. **`run_amazon_workflow.py`**
   - Added UTF-8 encoding setup at startup
   - Sets environment variables for subprocess calls

3. **`tapps_agents/agents/reviewer/scoring.py`** (v2.0.6+)
   - Added UTF-8 encoding to all subprocess.run() calls
   - Prevents UnicodeDecodeError when reading tool output

4. **`tapps_agents/agents/reviewer/typescript_scorer.py`** (v2.0.6+)
   - Added UTF-8 encoding to all subprocess.run() calls
   - Prevents UnicodeDecodeError when reading tool output

5. **`tapps_agents/core/background_wrapper.py`** (v2.0.6+)
   - Added visible execution indicators for background agents
   - Clear start/end indicators printed to stderr

6. **`windows_compatibility_check.py`** (New)
   - Diagnostic tool to verify Windows compatibility
   - Checks encoding, Unicode support, and path handling

## Known Limitations

1. **Progress Bars:** Unicode block characters (█, ░) may not display correctly in some Windows terminals. The fallback mechanism handles this automatically.

2. **Emojis:** Emojis in status messages may appear as `?` in older Windows terminals. The encoding fix handles this gracefully.

3. **PowerShell vs CMD:** PowerShell generally handles Unicode better than CMD. If issues persist, try using PowerShell.

## Testing

To verify everything works:

```powershell
# 1. Run compatibility check
python windows_compatibility_check.py

# 2. Run a simple workflow
python run_amazon_workflow.py

# 3. Check for any encoding errors in output
```

## Troubleshooting

### Issue: Still seeing encoding errors

**Solution:** Ensure `PYTHONIOENCODING=utf-8` is set before running:
```powershell
$env:PYTHONIOENCODING='utf-8'
python run_amazon_workflow.py
```

### Issue: Progress bars show as question marks

**Solution:** This is expected in some terminals. The workflow will still function correctly. The fix in `cursor_chat.py` handles this automatically.

### Issue: Workflow fails with encoding error

**Solution:** 
1. Check that you're using the updated `cursor_chat.py` with the encoding fix
2. Verify `PYTHONIOENCODING` is set
3. Try running with the helper script: `python run_amazon_workflow.py`

## Additional Notes

- The fixes are backward compatible and don't affect non-Windows systems
- The encoding fallback is automatic and doesn't require user intervention
- All workflow functionality remains intact; only display formatting is affected

