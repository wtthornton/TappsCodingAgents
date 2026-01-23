#!/usr/bin/env python3
"""
Update Context7 API Key in MCP Config

This script updates the MCP config file with the actual Context7 API key
from either environment variable or encrypted storage.

Note: Storing the API key directly in the config file is less secure than
using environment variables, but may be necessary if Cursor's MCP server
doesn't support environment variable template substitution.
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


def get_api_key() -> str | None:
    """Get Context7 API key from environment or encrypted storage."""
    # First try environment variable
    api_key = os.getenv("CONTEXT7_API_KEY")
    if api_key:
        return api_key
    
    # Try encrypted storage
    try:
        from tapps_agents.context7.backup_client import _ensure_context7_api_key
        api_key = _ensure_context7_api_key()
        if api_key:
            return api_key
    except Exception as e:
        print(f"[WARN] Could not load from encrypted storage: {e}", file=sys.stderr)
    
    return None


def update_mcp_config(mcp_file: Path, api_key: str) -> bool:
    """Update MCP config with actual API key."""
    try:
        # Read existing config
        with open(mcp_file, encoding="utf-8-sig") as f:
            config = json.load(f)
        
        # Ensure mcpServers section exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        # Ensure Context7 server config exists
        if "Context7" not in config["mcpServers"]:
            config["mcpServers"]["Context7"] = {
                "command": "npx",
                "args": ["-y", "@context7/mcp-server"],
                "env": {}
            }
        
        # Ensure env section exists
        if "env" not in config["mcpServers"]["Context7"]:
            config["mcpServers"]["Context7"]["env"] = {}
        
        # Update API key
        config["mcpServers"]["Context7"]["env"]["CONTEXT7_API_KEY"] = api_key
        
        # Write back
        with open(mcp_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update config: {e}", file=sys.stderr)
        return False


def main():
    """Main function."""
    print("=" * 70)
    print("Context7 MCP Config API Key Update")
    print("=" * 70)
    print()
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] Context7 API key not found in:")
        print("  1. CONTEXT7_API_KEY environment variable")
        print("  2. Encrypted storage (.tapps-agents/api-keys.encrypted)")
        print()
        print("Please set the API key first:")
        print("  PowerShell: $env:CONTEXT7_API_KEY='your-api-key'")
        print("  Bash: export CONTEXT7_API_KEY='your-api-key'")
        return 1
    
    masked_key = api_key[:10] + "..." if len(api_key) > 10 else api_key
    print(f"[OK] Found API key: {masked_key}")
    print()
    
    # Find MCP config file
    project_root = Path.cwd()
    mcp_file = project_root / ".cursor" / "mcp.json"
    
    if not mcp_file.exists():
        print(f"[ERROR] MCP config file not found: {mcp_file}")
        print("Run 'tapps-agents init' to create it first.")
        return 1
    
    print(f"[INFO] Found MCP config: {mcp_file}")
    
    # Confirm update
    print()
    print("[WARN] This will store the API key directly in the config file.")
    print("This is less secure than using environment variables, but may be")
    print("necessary if Cursor's MCP server doesn't support ${} template syntax.")
    print()
    response = input("Continue? (y/n): ").strip().lower()
    
    if response != 'y':
        print("[INFO] Update cancelled.")
        return 0
    
    # Update config
    if update_mcp_config(mcp_file, api_key):
        print()
        print("[OK] MCP config updated successfully!")
        print()
        print("Next steps:")
        print("  1. Restart Cursor completely for changes to take effect")
        print("  2. Check MCP server status in Cursor Settings")
        print()
        return 0
    else:
        print()
        print("[ERROR] Failed to update MCP config")
        return 1


if __name__ == "__main__":
    sys.exit(main())