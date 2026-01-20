# MCP Tools Troubleshooting Guide

This guide helps you diagnose and fix issues with MCP (Model Context Protocol) tools in Cursor, specifically Context7 and other MCP servers.

## Quick Diagnostic

Run the diagnostic script to check your MCP configuration:

```bash
python scripts/check_mcp_tools.py
```

Or use the fix script for Context7:

```bash
python scripts/fix_context7_mcp.py
```

## Common Issues

### Issue 1: Context7 Shows "Error" in Cursor Settings

**Symptoms:**
- Context7 MCP server shows "Error - Show Output" in Cursor Settings
- Red dot next to Context7 status

**Causes:**
1. `CONTEXT7_API_KEY` environment variable not set
2. `npx` not available (Node.js not installed)
3. MCP configuration file has incorrect format

**Solution:**

#### Step 1: Check API Key

The Context7 MCP server requires an API key. Check if it's set:

**PowerShell:**
```powershell
$env:CONTEXT7_API_KEY
```

**Bash/Zsh:**
```bash
echo $CONTEXT7_API_KEY
```

If empty, set it:

**PowerShell (current session):**
```powershell
$env:CONTEXT7_API_KEY='your-api-key-here'
```

**PowerShell (permanent - user level):**
```powershell
[System.Environment]::SetEnvironmentVariable('CONTEXT7_API_KEY', 'your-api-key-here', 'User')
```

**Bash/Zsh:**
```bash
export CONTEXT7_API_KEY='your-api-key-here'
# Add to ~/.bashrc or ~/.zshrc for persistence
```

#### Step 2: Check MCP Configuration

The MCP config file should be at `.cursor/mcp.json` (project-local) or `~/.cursor/mcp.json` (user-global).

Expected configuration:

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

**Note:** The `${CONTEXT7_API_KEY}` syntax references the environment variable. If the env var is not set, the MCP server will fail.

**Alternative:** If you can't set the environment variable, you can use a direct value (less secure):

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

#### Step 3: Check Node.js/npx

The Context7 MCP server requires `npx` (Node Package eXecute) which comes with Node.js.

Check if `npx` is available:

```bash
npx --version
```

If not available, install Node.js:
- Download from: https://nodejs.org/
- Or use a package manager:
  - Windows: `winget install OpenJS.NodeJS`
  - macOS: `brew install node`
  - Linux: `sudo apt install nodejs npm`

#### Step 4: Restart Cursor

After making changes:
1. Close Cursor completely
2. Reopen Cursor
3. Check Settings > Tools & MCP > Context7 status

### Issue 2: npx Not Available

**Symptoms:**
- Diagnostic script shows "npx not available"
- MCP servers fail to start

**Solution:**

Install Node.js (which includes `npx`):

**Windows:**
```powershell
winget install OpenJS.NodeJS
```

**macOS:**
```bash
brew install node
```

**Linux:**
```bash
sudo apt install nodejs npm
```

After installation, verify:
```bash
node --version
npm --version
npx --version
```

### Issue 3: Multiple MCP Config Files

**Symptoms:**
- Multiple `.cursor/mcp.json` files found
- Conflicting configurations

**Solution:**

MCP config files are checked in this order (first found wins):
1. `.cursor/mcp.json` (project-local) - **Recommended**
2. `~/.cursor/mcp.json` (user-global)
3. `~/.config/cursor/mcp.json` (user-global)

**Best Practice:** Use project-local `.cursor/mcp.json` for project-specific configurations. Use user-global configs only for personal preferences.

### Issue 4: MCP Server Not Starting

**Symptoms:**
- MCP server shows as "Error" but API key is set
- No tools available from MCP server

**Troubleshooting Steps:**

1. **Check Cursor MCP Logs:**
   - View > Output
   - Select "MCP" from the dropdown
   - Look for error messages

2. **Verify API Key Format:**
   - API key should not have quotes or extra spaces
   - Check for typos

3. **Test MCP Server Manually:**
   ```bash
   npx -y @context7/mcp-server
   ```
   (This may not work directly, but helps verify npx can find the package)

4. **Check Network Connectivity:**
   - Ensure you can access `context7.com`
   - Check firewall/proxy settings

5. **Verify Package Installation:**
   ```bash
   npm list -g @context7/mcp-server
   ```
   (Not required, as `npx -y` installs on-demand)

### Issue 5: Duplicate MCP Servers (context7/Context7, playwright/Playwright)

**Symptoms:**
- In Cursor Settings > Tools & MCP you see two Context7 entries (e.g. `context7` and `Context7`) and/or two Playwright entries (`playwright` and `Playwright`)
- One Context7 may show "Error - Show Output" while the other works

**Cause:**

Cursor loads **both** your **user-level** and **project-level** MCP configs and merges them. Server names are case-sensitive, so you get duplicates when:

- **User-level** `~/.cursor/mcp.json` (Windows: `%USERPROFILE%\.cursor\mcp.json`) defines `context7` and `playwright` (lowercase)
- **Project-level** `.cursor/mcp.json` defines `Context7` and `Playwright` (uppercase), e.g. from `tapps-agents init`

The `Context7` (uppercase) entry often errors because it uses `@context7/mcp-server` with `CONTEXT7_API_KEY` from the environment. If that env var is not set when Cursor starts the project MCP, that instance fails. Your user-level `context7` may use a different package or inline API key and work correctly.

**Fix: Use a single source for each server**

1. **Option A – Prefer user-level (simplest if it already works)**  
   Remove `Context7` and `Playwright` from the **project** `.cursor/mcp.json` so only your user-level `context7` and `playwright` are used:
   - Edit `c:\cursor\TappsCodingAgents\.cursor\mcp.json` and delete the `"Context7"` and `"Playwright"` entries, or set `"mcpServers": {}` if you have no other project-specific servers.

2. **Option B – Prefer project-level**  
   Remove `context7` and `playwright` from **user-level** `~/.cursor/mcp.json`. Keep only `Context7` and `Playwright` in the project `.cursor/mcp.json`. Ensure `CONTEXT7_API_KEY` is set (and that `Context7` uses `@context7/mcp-server` with that env, or an equivalent working config).

3. **Restart Cursor** after edits.

**Best practice:** Avoid defining the same logical MCP server in both user and project configs. Use project-level for repo-specific setup, user-level for tools you want in all projects.

## MCP Tools Available

### Context7
- **Purpose:** Library documentation lookup
- **Tools:** `resolve-library-id`, `get-library-docs`
- **Required:** `CONTEXT7_API_KEY` environment variable
- **Command:** `npx -y @context7/mcp-server`

### Playwright
- **Purpose:** Browser automation
- **Tools:** Browser navigation, screenshots, form filling, etc.
- **Required:** None (optional)
- **Command:** `npx -y @playwright/mcp@latest`

### TestSprite
- **Purpose:** Test generation and management
- **Tools:** Test generation, execution, reporting
- **Required:** TestSprite configuration
- **Command:** `npx -y @testsprite/testsprite-mcp@latest`

## Verification

After fixing configuration issues, verify MCP tools are working:

1. **In Cursor Settings:**
   - Go to Settings > Tools & MCP
   - Check that Context7 shows "X tools enabled" (not "Error")

2. **In Cursor Chat:**
   - Try: `@reviewer *docs fastapi`
   - Should return library documentation

3. **Using Diagnostic Script:**
   ```bash
   python scripts/check_mcp_tools.py
   ```
   Should show all servers as properly configured.

## Getting Help

If issues persist:

1. Run diagnostic: `python scripts/check_mcp_tools.py`
2. Check Cursor MCP logs (View > Output > MCP)
3. Verify environment variables are set correctly
4. Ensure Node.js/npx is installed and in PATH
5. Restart Cursor completely

## Related Documentation

- [Context7 Integration Guide](../docs/CONTEXT7_INTEGRATION.md)
- [MCP Server Setup](../docs/MCP_SERVER_SETUP.md)
- [Cursor Integration Guide](../docs/CURSOR_AI_INTEGRATION_PLAN_2025.md)
