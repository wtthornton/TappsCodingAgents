# Context7 MCP Server Error Troubleshooting

## Problem: Context7 MCP Server Shows "Error - Show Output" in Cursor

When Context7 MCP server fails to start in Cursor, you'll see a red error indicator and "Error - Show Output" status in the MCP settings panel.

## Common Causes and Solutions

### 1. Missing CONTEXT7_API_KEY Environment Variable

**Symptoms:**
- MCP server shows error status
- Error output mentions "API key" or "authentication"
- Server starts but immediately exits

**Solution:**

**Option A: Set Environment Variable (Recommended)**

**Windows (PowerShell):**
```powershell
# For current session
$env:CONTEXT7_API_KEY = "your-api-key-here"

# For permanent (User-level)
[System.Environment]::SetEnvironmentVariable("CONTEXT7_API_KEY", "your-api-key-here", "User")
```

**Windows (CMD):**
```cmd
setx CONTEXT7_API_KEY "your-api-key-here"
```

**Linux/Mac:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export CONTEXT7_API_KEY="your-api-key-here"

# Or for current session
export CONTEXT7_API_KEY="your-api-key-here"
```

**Important:** After setting the environment variable, **restart Cursor completely** (not just reload window) for the change to take effect.

**Option B: Set in mcp.json (Alternative)**

Edit `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "Context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "your-actual-api-key-here"
      }
    }
  }
}
```

**Note:** This embeds the API key in the file. Use environment variable (Option A) for better security.

### 2. NPX Not Found or Not Working

**Symptoms:**
- Error mentions "npx" or "command not found"
- Error output shows "spawn npx ENOENT"
- Node.js might not be installed

**Solution:**

**Check if Node.js is installed:**
```bash
node --version
npm --version
npx --version
```

**If not installed:**
1. Download and install Node.js from https://nodejs.org/
2. Install LTS version (recommended)
3. Restart Cursor after installation

**Verify npx works:**
```bash
npx --version
# Should output version number, not an error
```

### 3. @context7/mcp-server Package Installation Failure

**Symptoms:**
- Error mentions "@context7/mcp-server"
- Error shows "package not found" or "install failed"
- Network connectivity issues

**Solution:**

**Test manual installation:**
```bash
npx -y @context7/mcp-server --version
```

**If this fails:**
1. **Check internet connection** - npx needs to download the package
2. **Check npm registry** - Ensure you can access npm registry:
   ```bash
   npm config get registry
   # Should output: https://registry.npmjs.org/
   ```
3. **Clear npm cache** (if needed):
   ```bash
   npm cache clean --force
   ```
4. **Try with verbose logging**:
   ```bash
   npx --verbose -y @context7/mcp-server
   ```

### 4. Invalid API Key

**Symptoms:**
- Server starts but immediately fails
- Error mentions "authentication" or "unauthorized"
- API key format might be wrong

**Solution:**

1. **Verify API key format:**
   - Should be a string (no quotes in environment variable)
   - Should not have leading/trailing spaces
   - Should be the actual key, not a reference like `${CONTEXT7_API_KEY}`

2. **Test API key manually:**
   ```bash
   # Set key temporarily
   export CONTEXT7_API_KEY="your-key"
   
   # Test with curl (Linux/Mac)
   curl -H "Authorization: Bearer $CONTEXT7_API_KEY" https://api.context7.com/v1/health
   
   # Or test via npx
   npx -y @context7/mcp-server --help
   ```

3. **Get new API key:**
   - Visit Context7 website
   - Generate a new API key
   - Update environment variable
   - Restart Cursor

### 5. Port/Network Conflicts

**Symptoms:**
- Server tries to start but fails with port errors
- Connection refused errors
- Timeout errors

**Solution:**

1. **Check for port conflicts:**
   - MCP servers use stdio (standard input/output), not network ports
   - If you see port errors, might be a different issue

2. **Check firewall/antivirus:**
   - Temporarily disable to test
   - Add Cursor and Node.js to exceptions

### 6. Configuration Format Errors

**Symptoms:**
- Error on Cursor startup
- MCP configuration not loading
- JSON parse errors

**Solution:**

**Verify `.cursor/mcp.json` format:**
```json
{
  "mcpServers": {
    "Context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
      }
    }
  }
}
```

**Common mistakes:**
- ❌ Missing quotes around keys/values
- ❌ Trailing commas in JSON
- ❌ Wrong nesting structure
- ❌ Using `mcp_servers` instead of `mcpServers` (camelCase required)

**Validate JSON:**
```bash
# Linux/Mac
cat .cursor/mcp.json | python -m json.tool

# Or use online JSON validator
```

### 7. Cursor-Specific Issues

**Symptoms:**
- Configuration looks correct but still fails
- Other MCP servers work but Context7 doesn't
- Cursor restart doesn't help

**Solution:**

1. **Reload Cursor Window:**
   - `Ctrl+Shift+P` (Cmd+Shift+P on Mac)
   - Type "Reload Window"
   - Select "Developer: Reload Window"

2. **Restart Cursor completely:**
   - Close all Cursor windows
   - Wait a few seconds
   - Reopen Cursor

3. **Check Cursor logs:**
   - Open Output panel (`Ctrl+Shift+U` or View > Output)
   - Select "MCP" from dropdown
   - Look for Context7 error messages

4. **Verify MCP settings location:**
   - Cursor might use different config location
   - Check: `%APPDATA%\Cursor\User\settings.json` (Windows)
   - Or: `~/.config/Cursor/User/settings.json` (Linux/Mac)

## Diagnostic Steps

### Step 1: Check MCP Server Configuration

```bash
# Verify mcp.json exists
cat .cursor/mcp.json

# Or on Windows
type .cursor\mcp.json
```

### Step 2: Verify Environment Variable

**Windows (PowerShell):**
```powershell
$env:CONTEXT7_API_KEY
```

**Windows (CMD):**
```cmd
echo %CONTEXT7_API_KEY%
```

**Linux/Mac:**
```bash
echo $CONTEXT7_API_KEY
```

**Important:** If variable is not set, Cursor won't be able to start the MCP server.

### Step 3: Test NPX Installation

```bash
# Test npx works
npx --version

# Test Context7 package installation
npx -y @context7/mcp-server --help
```

### Step 4: Check Cursor Output

1. Open Output panel in Cursor (`Ctrl+Shift+U`)
2. Select "MCP" from dropdown
3. Look for Context7 error messages
4. Copy error message for troubleshooting

### Step 5: Manual Server Test

```bash
# Set API key
export CONTEXT7_API_KEY="your-key"

# Try to run server directly
npx -y @context7/mcp-server

# Should start and wait for input (stdio mode)
# Press Ctrl+C to stop
```

## Quick Fix Checklist

- [ ] `CONTEXT7_API_KEY` environment variable is set
- [ ] Environment variable has no quotes around the value
- [ ] Cursor was restarted after setting environment variable
- [ ] Node.js and npm are installed (`node --version`, `npm --version`)
- [ ] npx is working (`npx --version`)
- [ ] `.cursor/mcp.json` has correct JSON format
- [ ] Internet connection is working (for npx package download)
- [ ] API key is valid (not expired, correct format)
- [ ] No firewall/antivirus blocking Node.js
- [ ] Cursor Output panel checked for specific error messages

## Re-initialize MCP Configuration

If all else fails, recreate the MCP configuration:

```bash
# Run init command (will recreate mcp.json if needed)
tapps-agents init --reset-mcp

# Or manually delete and recreate
rm .cursor/mcp.json  # Linux/Mac
del .cursor\mcp.json  # Windows

# Then run init
tapps-agents init
```

## Getting Help

If the issue persists:

1. **Check Cursor Output Logs:**
   - Open Output panel (`Ctrl+Shift+U`)
   - Select "MCP" from dropdown
   - Copy full error message

2. **Check System Logs:**
   - Windows Event Viewer (if applicable)
   - System logs for Node.js errors

3. **Test with Minimal Config:**
   ```json
   {
     "mcpServers": {
       "Context7": {
         "command": "npx",
         "args": ["-y", "@context7/mcp-server"],
         "env": {
           "CONTEXT7_API_KEY": "your-actual-key-here"
         }
       }
     }
   }
   ```

4. **Disable Context7 Temporarily:**
   - If you don't need Context7 immediately, you can disable it
   - Edit `.tapps-agents/config.yaml`:
     ```yaml
     context7:
       enabled: false
     ```
   - TappsCodingAgents will work without Context7 (just missing library-specific guidance)

## Alternative: Use HTTP Fallback

If MCP server continues to fail, you can use HTTP fallback (requires API key):

1. **Set environment variable:**
   ```bash
   export CONTEXT7_API_KEY="your-key"
   ```

2. **Disable MCP in config** (optional):
   - TappsCodingAgents will automatically fall back to HTTP if MCP is not available

3. **HTTP fallback will be used automatically:**
   - No MCP server needed
   - Direct API calls via HTTP
   - Same functionality, just different transport

## Expected Behavior When Working

When Context7 MCP server is working correctly:

- ✅ Green status dot in Cursor MCP settings
- ✅ "X tools enabled" message (not error)
- ✅ No error messages in Output panel
- ✅ Context7 library lookups work in reviewer agent
- ✅ No "Context7 lookup failed" warnings (unless library not in database)

## Summary

Most Context7 MCP server errors are caused by:
1. **Missing API key** (90% of cases) - Set `CONTEXT7_API_KEY` environment variable
2. **Node.js/npx not installed** - Install Node.js from nodejs.org
3. **Invalid JSON in mcp.json** - Validate JSON format
4. **Cursor not restarted** - Restart Cursor after changing environment variables

**Most common fix:** Set `CONTEXT7_API_KEY` environment variable and restart Cursor completely.

## Related Documentation

- [Context7 Library Resolution Issues](CONTEXT7_LIBRARY_RESOLUTION_ISSUES.md)
- [Context7 Integration Guide](TAPPS_AGENTS_CONTEXT7_AUTO_ENHANCEMENT.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

