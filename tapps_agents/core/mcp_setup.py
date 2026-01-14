"""
MCP Setup Helper Functions

Provides interactive setup and validation for MCP servers.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# Windows encoding fix
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def offer_context7_setup(project_root: Path, interactive: bool = True) -> bool:
    """
    Offer to set up Context7 API key interactively.
    
    Args:
        project_root: Project root directory
        interactive: Whether to prompt user (default: True)
    
    Returns:
        True if setup was completed, False otherwise
    """
    if not interactive:
        return False
    
    api_key = os.getenv("CONTEXT7_API_KEY")
    if api_key:
        return True  # Already set
    
    print("\n" + "=" * 60)
    print("Context7 API Key Setup")
    print("=" * 60)
    print()
    print("Context7 MCP server requires an API key to work.")
    print("You can:")
    print("  1. Set environment variable (recommended)")
    print("  2. Add API key directly to MCP config (less secure)")
    print("  3. Skip for now (you can set it later)")
    print()
    
    try:
        choice = input("Choose option [1/2/3]: ").strip()
        
        if choice == "1":
            print("\nTo set environment variable:")
            if sys.platform == "win32":
                print("  PowerShell (current session):")
                print("    $env:CONTEXT7_API_KEY='your-api-key'")
                print("\n  PowerShell (permanent):")
                print("    [System.Environment]::SetEnvironmentVariable('CONTEXT7_API_KEY', 'your-api-key', 'User')")
            else:
                print("  export CONTEXT7_API_KEY='your-api-key'")
                print("  # Add to ~/.bashrc or ~/.zshrc for persistence")
            print("\nAfter setting, restart Cursor for changes to take effect.")
            return False  # User needs to set it manually
        
        elif choice == "2":
            api_key = input("Enter your Context7 API key: ").strip()
            if api_key:
                # Update MCP config with direct value
                mcp_file = project_root / ".cursor" / "mcp.json"
                if mcp_file.exists():
                    try:
                        with open(mcp_file, encoding="utf-8-sig") as f:
                            config = json.load(f)
                        
                        mcp_servers = config.get("mcpServers", {})
                        if "Context7" in mcp_servers:
                            mcp_servers["Context7"]["env"]["CONTEXT7_API_KEY"] = api_key
                            
                            with open(mcp_file, "w", encoding="utf-8") as f:
                                json.dump(config, f, indent=2)
                                f.write("\n")
                            
                            print("\n[OK] API key added to MCP config")
                            print("[WARN] Note: API key is stored in plain text. Consider using environment variable for better security.")
                            return True
                    except Exception as e:
                        print(f"\n[ERROR] Failed to update MCP config: {e}")
                        return False
                else:
                    print("\n[ERROR] MCP config file not found")
                    return False
        
        # Choice 3 or invalid - skip
        print("\n[WARN] Skipping API key setup. Context7 MCP server will not work until API key is configured.")
        return False
        
    except (EOFError, KeyboardInterrupt):
        print("\n[WARN] Setup cancelled. You can configure API key later.")
        return False
