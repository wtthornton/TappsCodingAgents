#!/usr/bin/env python3
"""
Inject MCP API Keys from Encrypted Storage into MCP Config

This script loads API keys from encrypted storage and injects them
directly into the MCP config file. Use this if Cursor's MCP server
doesn't support ${VAR} environment variable substitution syntax.

⚠️  WARNING: This stores keys in plain text (less secure than env vars)
"""

import json
import sys
from pathlib import Path

# Windows encoding fix
if sys.platform == "win32":
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def main():
    """Main function."""
    project_root = Path.cwd()
    sys.path.insert(0, str(project_root))
    
    # Load keys from encrypted storage
    try:
        from tapps_agents.context7.security import APIKeyManager
        
        key_manager = APIKeyManager(project_root / ".tapps-agents")
        context7_key = key_manager.load_api_key("context7")
        github_key = key_manager.load_api_key("github")
    except Exception as e:
        print(f"[ERROR] Failed to load keys: {e}", file=sys.stderr)
        return 1
    
    # Read MCP config
    mcp_file = project_root / ".cursor" / "mcp.json"
    if not mcp_file.exists():
        print(f"[ERROR] MCP config not found: {mcp_file}", file=sys.stderr)
        return 1
    
    try:
        with open(mcp_file, encoding="utf-8-sig") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read MCP config: {e}", file=sys.stderr)
        return 1
    
    # Inject keys
    mcp_servers = config.setdefault("mcpServers", {})
    updated = False
    
    if context7_key:
        if "Context7" not in mcp_servers:
            mcp_servers["Context7"] = {
                "command": "npx",
                "args": ["-y", "@context7/mcp-server"],
                "env": {}
            }
        env = mcp_servers["Context7"].setdefault("env", {})
        if env.get("CONTEXT7_API_KEY") != context7_key:
            env["CONTEXT7_API_KEY"] = context7_key
            updated = True
    
    if github_key:
        if "GitHub" not in mcp_servers:
            mcp_servers["GitHub"] = {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {}
            }
        env = mcp_servers["GitHub"].setdefault("env", {})
        if env.get("GITHUB_PERSONAL_ACCESS_TOKEN") != github_key:
            env["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_key
            updated = True
    
    if updated:
        # Write back
        try:
            with open(mcp_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
                f.write("\n")
            print("[OK] Injected API keys into MCP config", file=sys.stderr)
            print("[WARN] Keys are now in plain text in the config file", file=sys.stderr)
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to write MCP config: {e}", file=sys.stderr)
            return 1
    else:
        print("[INFO] MCP config already has keys", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())