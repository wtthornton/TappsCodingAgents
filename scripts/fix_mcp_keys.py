#!/usr/bin/env python3
"""
Fix MCP Keys - Inject actual API keys into MCP config

This script injects actual API key values into the MCP config file,
replacing ${VAR} placeholders with actual values from environment or encrypted storage.
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
    project_root = Path.cwd()
    mcp_file = project_root / ".cursor" / "mcp.json"
    
    if not mcp_file.exists():
        print(f"[ERROR] MCP config not found: {mcp_file}", file=sys.stderr)
        return 1
    
    # Read current config
    try:
        with open(mcp_file, encoding="utf-8-sig") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read MCP config: {e}", file=sys.stderr)
        return 1
    
    mcp_servers = config.setdefault("mcpServers", {})
    updated = False
    
    # Get Context7 key
    if "Context7" in mcp_servers:
        env_vars = mcp_servers["Context7"].setdefault("env", {})
        current_key = env_vars.get("CONTEXT7_API_KEY", "")
        
        # If it's a placeholder, try to get actual value
        if current_key == "${CONTEXT7_API_KEY}" or current_key.startswith("${"):
            # Try environment variable first
            actual_key = os.getenv("CONTEXT7_API_KEY")
            
            # If not in env, try encrypted storage
            if not actual_key:
                try:
                    sys.path.insert(0, str(project_root))
                    from tapps_agents.context7.security import APIKeyManager
                    key_manager = APIKeyManager(project_root / ".tapps-agents")
                    actual_key = key_manager.load_api_key("context7")
                except Exception:
                    pass
            
            if actual_key:
                env_vars["CONTEXT7_API_KEY"] = actual_key
                updated = True
                print("[OK] Injected Context7 API key", file=sys.stderr)
            else:
                print("[WARN] Context7 API key not found in env or storage", file=sys.stderr)
    
    # Get GitHub key
    if "GitHub" in mcp_servers:
        env_vars = mcp_servers["GitHub"].setdefault("env", {})
        current_key = env_vars.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")
        
        # If it's a placeholder, try to get actual value
        if current_key == "${GITHUB_PERSONAL_ACCESS_TOKEN}" or current_key.startswith("${"):
            # Try environment variable first
            actual_key = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
            
            # If not in env, try encrypted storage
            if not actual_key:
                try:
                    sys.path.insert(0, str(project_root))
                    from tapps_agents.context7.security import APIKeyManager
                    key_manager = APIKeyManager(project_root / ".tapps-agents")
                    actual_key = key_manager.load_api_key("github")
                except Exception:
                    pass
            
            if actual_key:
                env_vars["GITHUB_PERSONAL_ACCESS_TOKEN"] = actual_key
                updated = True
                print("[OK] Injected GitHub API key", file=sys.stderr)
            else:
                print("[WARN] GitHub API key not found in env or storage", file=sys.stderr)
    
    if updated:
        # Write back
        try:
            with open(mcp_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
                f.write("\n")
            print("[OK] MCP config updated with actual API keys", file=sys.stderr)
            print("[WARN] Keys are now in plain text in the config file", file=sys.stderr)
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to write MCP config: {e}", file=sys.stderr)
            return 1
    else:
        print("[INFO] No keys needed to be updated", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
