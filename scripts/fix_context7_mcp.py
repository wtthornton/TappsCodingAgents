#!/usr/bin/env python3
"""
Fix Context7 MCP Configuration

This script helps fix Context7 MCP server configuration issues by:
1. Checking if CONTEXT7_API_KEY environment variable is set
2. Providing options to fix the configuration
3. Optionally updating the MCP config file
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


def find_mcp_config() -> Path | None:
    """Find the project-local MCP config file."""
    project_root = Path.cwd()
    mcp_file = project_root / ".cursor" / "mcp.json"
    if mcp_file.exists():
        return mcp_file
    return None


def check_api_key() -> tuple[bool, str | None]:
    """Check if CONTEXT7_API_KEY is set."""
    api_key = os.getenv("CONTEXT7_API_KEY")
    if api_key:
        masked = api_key[:10] + "..." if len(api_key) > 10 else api_key[:len(api_key)]
        return True, masked
    return False, None


def update_mcp_config_with_env_var(mcp_file: Path) -> bool:
    """Update MCP config to use environment variable reference."""
    try:
        with open(mcp_file, encoding="utf-8-sig") as f:
            config = json.load(f)
        
        mcp_servers = config.get("mcpServers", {})
        if "Context7" not in mcp_servers:
            mcp_servers["Context7"] = {
                "command": "npx",
                "args": ["-y", "@context7/mcp-server"],
                "env": {}
            }
        
        # Update to use environment variable reference
        mcp_servers["Context7"]["env"]["CONTEXT7_API_KEY"] = "${CONTEXT7_API_KEY}"
        
        # Write back
        with open(mcp_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
        
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update config: {e}")
        return False


def main():
    """Main function."""
    print("=" * 70)
    print("Context7 MCP Configuration Fix")
    print("=" * 70)
    print()
    
    # Check if API key is set
    has_key, masked_value = check_api_key()
    if has_key:
        print(f"[OK] CONTEXT7_API_KEY is set (value: {masked_value})")
        print()
        print("Your API key is configured. The MCP server should work if:")
        print("  1. Node.js and npx are installed")
        print("  2. Cursor is restarted after setting the environment variable")
        print()
        
        # Check MCP config
        mcp_file = find_mcp_config()
        if mcp_file:
            print(f"[INFO] Found MCP config: {mcp_file}")
            with open(mcp_file, encoding="utf-8-sig") as f:
                config = json.load(f)
            
            context7_config = config.get("mcpServers", {}).get("Context7", {})
            env_vars = context7_config.get("env", {})
            api_key_ref = env_vars.get("CONTEXT7_API_KEY", "")
            
            if api_key_ref == "${CONTEXT7_API_KEY}":
                print("[OK] MCP config correctly references environment variable")
                return 0
            elif not api_key_ref:
                print("[WARN] MCP config missing CONTEXT7_API_KEY reference")
                print("Updating config to use environment variable...")
                if update_mcp_config_with_env_var(mcp_file):
                    print("[OK] Config updated successfully")
                    print("Please restart Cursor for changes to take effect.")
                    return 0
                else:
                    return 1
            else:
                print("[INFO] MCP config has direct API key value (not using env var)")
                print("This is less secure but will work.")
                return 0
        else:
            print("[WARN] No project-local MCP config found")
            print("Run 'tapps-agents init' to create one.")
            return 1
    else:
        print("[ERROR] CONTEXT7_API_KEY environment variable is not set")
        print()
        print("To fix this, you have two options:")
        print()
        print("Option 1: Set environment variable (recommended)")
        print("  PowerShell (current session):")
        print("    $env:CONTEXT7_API_KEY='your-api-key-here'")
        print()
        print("  PowerShell (permanent - user level):")
        print("    [System.Environment]::SetEnvironmentVariable('CONTEXT7_API_KEY', 'your-api-key-here', 'User')")
        print()
        print("  Bash/Zsh:")
        print("    export CONTEXT7_API_KEY='your-api-key-here'")
        print("    # Add to ~/.bashrc or ~/.zshrc for persistence")
        print()
        print("Option 2: Update .cursor/mcp.json with direct value")
        print("  (Less secure, but works if env var not available)")
        print()
        
        mcp_file = find_mcp_config()
        if mcp_file:
            print(f"[INFO] Found MCP config: {mcp_file}")
            response = input("Do you want to update the config file now? (y/n): ").strip().lower()
            if response == 'y':
                api_key = input("Enter your Context7 API key: ").strip()
                if api_key:
                    try:
                        with open(mcp_file, encoding="utf-8-sig") as f:
                            config = json.load(f)
                        
                        mcp_servers = config.get("mcpServers", {})
                        if "Context7" not in mcp_servers:
                            mcp_servers["Context7"] = {
                                "command": "npx",
                                "args": ["-y", "@context7/mcp-server"],
                                "env": {}
                            }
                        
                        mcp_servers["Context7"]["env"]["CONTEXT7_API_KEY"] = api_key
                        
                        with open(mcp_file, "w", encoding="utf-8") as f:
                            json.dump(config, f, indent=2)
                            f.write("\n")
                        
                        print("[OK] Config updated with API key")
                        print("Please restart Cursor for changes to take effect.")
                        return 0
                    except Exception as e:
                        print(f"[ERROR] Failed to update config: {e}")
                        return 1
                else:
                    print("[ERROR] API key cannot be empty")
                    return 1
        else:
            print("[WARN] No project-local MCP config found")
            print("Run 'tapps-agents init' to create one.")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
