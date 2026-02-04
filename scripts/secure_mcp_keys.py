#!/usr/bin/env python3
"""
Secure MCP API Keys

This script:
1. Reads API keys from .cursor/mcp.json (currently stored in plain text)
2. Stores them in encrypted storage (.tapps-agents/api-keys.encrypted)
3. Updates MCP config to use environment variable references
4. Provides instructions for setting environment variables

Note: After running this, you'll need to set environment variables before
starting Cursor, or use a helper script to load them automatically.
"""

import json
import os
import sys
from pathlib import Path

# Windows encoding fix
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def main():
    """Main function."""
    print("=" * 70)
    print("Secure MCP API Keys")
    print("=" * 70)
    print()
    
    project_root = Path.cwd()
    mcp_file = project_root / ".cursor" / "mcp.json"
    
    if not mcp_file.exists():
        print(f"[ERROR] MCP config file not found: {mcp_file}")
        return 1
    
    # Read current MCP config
    try:
        with open(mcp_file, encoding="utf-8-sig") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read MCP config: {e}")
        return 1
    
    mcp_servers = config.get("mcpServers", {})
    
    # Extract keys
    context7_key = None
    github_key = None
    
    if "Context7" in mcp_servers:
        env_vars = mcp_servers["Context7"].get("env", {})
        context7_key = env_vars.get("CONTEXT7_API_KEY")
    
    if "GitHub" in mcp_servers:
        env_vars = mcp_servers["GitHub"].get("env", {})
        github_key = env_vars.get("GITHUB_PERSONAL_ACCESS_TOKEN")
    
    if not context7_key and not github_key:
        print("[INFO] No API keys found in MCP config to secure.")
        return 0
    
    # Add project root to path for imports
    sys.path.insert(0, str(project_root))
    
    # Import APIKeyManager
    try:
        from tapps_agents.context7.security import APIKeyManager
        
        key_manager = APIKeyManager(project_root / ".tapps-agents")
    except Exception as e:
        print(f"[ERROR] Failed to import APIKeyManager: {e}")
        print("Make sure you're running from the project root.")
        return 1
    
    # Store keys in encrypted storage
    stored_keys = []
    
    if context7_key:
        if not context7_key.startswith("${"):  # Only store if it's not already a reference
            try:
                key_manager.store_api_key("context7", context7_key, encrypt=True)
                stored_keys.append("Context7")
                print("[OK] Stored Context7 API key in encrypted storage")
            except Exception as e:
                print(f"[ERROR] Failed to store Context7 key: {e}")
                return 1
    
    if github_key:
        if not github_key.startswith("${"):  # Only store if it's not already a reference
            try:
                key_manager.store_api_key("github", github_key, encrypt=True)
                stored_keys.append("GitHub")
                print("[OK] Stored GitHub API key in encrypted storage")
            except Exception as e:
                print(f"[ERROR] Failed to store GitHub key: {e}")
                return 1
    
    if not stored_keys:
        print("[INFO] No keys needed to be stored (they may already be references).")
        return 0
    
    # Update MCP config to use environment variable references
    updated = False
    
    if context7_key and not context7_key.startswith("${"):
        if "Context7" not in mcp_servers:
            mcp_servers["Context7"] = {
                "command": "npx",
                "args": ["-y", "@context7/mcp-server"],
                "env": {}
            }
        if "env" not in mcp_servers["Context7"]:
            mcp_servers["Context7"]["env"] = {}
        mcp_servers["Context7"]["env"]["CONTEXT7_API_KEY"] = "${CONTEXT7_API_KEY}"
        updated = True
        print("[OK] Updated Context7 config to use environment variable reference")
    
    if github_key and not github_key.startswith("${"):
        if "GitHub" not in mcp_servers:
            mcp_servers["GitHub"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {}
            }
        if "env" not in mcp_servers["GitHub"]:
            mcp_servers["GitHub"]["env"] = {}
        mcp_servers["GitHub"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] = "${GITHUB_PERSONAL_ACCESS_TOKEN}"
        updated = True
        print("[OK] Updated GitHub config to use environment variable reference")
    
    # Write updated config
    if updated:
        try:
            with open(mcp_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
                f.write("\n")
            print()
            print("[OK] MCP config updated to use environment variable references")
        except Exception as e:
            print(f"[ERROR] Failed to write MCP config: {e}")
            print("[WARN] Keys are stored in encrypted storage, but MCP config not updated.")
            print("You may need to manually update the config file.")
            return 1
    
    # Create helper script to load keys into environment
    print()
    print("=" * 70)
    print("Next Steps")
    print("=" * 70)
    print()
    print("Keys have been secured and stored in encrypted storage.")
    print("To use them with Cursor MCP servers, you need to set environment variables.")
    print()
    
    # Check if we're on Windows
    is_windows = sys.platform == "win32"
    
    if is_windows:
        # Create PowerShell script
        ps_script = project_root / "scripts" / "load_mcp_keys.ps1"
        ps_content = '''# Load MCP API Keys from Encrypted Storage
# Run this script before starting Cursor, or add it to your PowerShell profile

$ErrorActionPreference = "Stop"

# Get project root (assuming script is in scripts/)
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Set PYTHONPATH if needed
$env:PYTHONPATH = "$ProjectRoot"

# Load keys using Python
$context7_key = python -c "import sys; sys.path.insert(0, '$ProjectRoot'); from tapps_agents.context7.security import APIKeyManager; from pathlib import Path; km = APIKeyManager(Path('$ProjectRoot') / '.tapps-agents'); key = km.load_api_key('context7'); print(key if key else '')" 2>$null
if ($context7_key) {
    $env:CONTEXT7_API_KEY = $context7_key
    Write-Host "[OK] Loaded Context7 API key" -ForegroundColor Green
}

$github_key = python -c "import sys; sys.path.insert(0, '$ProjectRoot'); from tapps_agents.context7.security import APIKeyManager; from pathlib import Path; km = APIKeyManager(Path('$ProjectRoot') / '.tapps-agents'); key = km.load_api_key('github'); print(key if key else '')" 2>$null
if ($github_key) {
    $env:GITHUB_PERSONAL_ACCESS_TOKEN = $github_key
    Write-Host "[OK] Loaded GitHub API key" -ForegroundColor Green
}

Write-Host ""
Write-Host "Environment variables set. You can now start Cursor." -ForegroundColor Cyan
Write-Host "To make this permanent, add this script to your PowerShell profile:" -ForegroundColor Yellow
Write-Host "  . $ps_script" -ForegroundColor Yellow
'''
        try:
            ps_script.write_text(ps_content, encoding="utf-8")
            print(f"[OK] Created PowerShell helper script: {ps_script}")
            print()
            print("To load keys before starting Cursor:")
            print(f"  . {ps_script}")
            print()
        except Exception as e:
            print(f"[WARN] Failed to create PowerShell script: {e}")
    
    # Also create a Python helper script (cross-platform)
    py_script = project_root / "scripts" / "load_mcp_keys.py"
    py_content = '''#!/usr/bin/env python3
"""
Load MCP API Keys from Encrypted Storage

Loads API keys from encrypted storage and sets them as environment variables.
Run this before starting Cursor, or source it in your shell.
"""

import os
import sys
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent

try:
    from tapps_agents.context7.security import APIKeyManager
    
    key_manager = APIKeyManager(project_root / ".tapps-agents")
    
    # Load Context7 key
    context7_key = key_manager.load_api_key("context7")
    if context7_key:
        os.environ["CONTEXT7_API_KEY"] = context7_key
        print("[OK] Loaded Context7 API key", file=sys.stderr)
    
    # Load GitHub key
    github_key = key_manager.load_api_key("github")
    if github_key:
        os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_key
        print("[OK] Loaded GitHub API key", file=sys.stderr)
    
    # Print export commands for shell sourcing
    if context7_key:
        print(f'export CONTEXT7_API_KEY="{context7_key}"')
    if github_key:
        print(f'export GITHUB_PERSONAL_ACCESS_TOKEN="{github_key}"')
    
except Exception as e:
    print(f"[ERROR] Failed to load keys: {e}", file=sys.stderr)
    sys.exit(1)
'''
    try:
        py_script.write_text(py_content, encoding="utf-8")
        # Make executable on Unix
        if sys.platform != "win32":
            os.chmod(py_script, 0o755)
        print(f"[OK] Created Python helper script: {py_script}")
        print()
        print("Usage:")
        if sys.platform == "win32":
            print(f"  python {py_script}")
        else:
            print(f"  eval $(python {py_script})")
        print()
    except Exception as e:
        print(f"[WARN] Failed to create Python script: {e}")
    
    print("=" * 70)
    print("Security Summary")
    print("=" * 70)
    print()
    print("✅ API keys removed from plain text MCP config")
    print("✅ Keys stored in encrypted storage (.tapps-agents/api-keys.encrypted)")
    print("✅ MCP config uses environment variable references")
    print()
    print("⚠️  IMPORTANT: Set environment variables before starting Cursor:")
    print()
    print("Option 1: Use helper scripts (recommended)")
    if is_windows:
        print("  PowerShell: . scripts/load_mcp_keys.ps1")
    print("  Python: eval $(python scripts/load_mcp_keys.py)")
    print()
    print("Option 2: Set manually")
    print("  PowerShell: $env:CONTEXT7_API_KEY='...'")
    print("  Bash: export CONTEXT7_API_KEY='...'")
    print()
    print("⚠️  Note: If Cursor's MCP server doesn't support ${} syntax, you may")
    print("    need to keep keys in the config file, but this is less secure.")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())