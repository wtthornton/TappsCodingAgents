#!/usr/bin/env python3
"""
MCP Tools Diagnostic Script

Checks the status of all MCP servers configured in Cursor and provides
diagnostic information and fixes for common issues.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# Windows encoding fix
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ASCII-safe symbols for Windows compatibility
OK = "[OK]"
ERROR = "[ERROR]"
WARNING = "[WARN]"
INFO = "[INFO]"
TOOL = "[TOOL]"
FILE = "[FILE]"


def find_mcp_config_files() -> list[Path]:
    """Find all possible MCP config file locations."""
    project_root = Path.cwd()
    config_paths = [
        project_root / ".cursor" / "mcp.json",
        project_root / ".vscode" / "mcp.json",
        Path.home() / ".cursor" / "mcp.json",
        Path.home() / ".config" / "cursor" / "mcp.json",
    ]
    return [p for p in config_paths if p.exists()]


def load_mcp_config(config_path: Path) -> dict[str, Any] | None:
    """Load MCP configuration from file."""
    try:
        with open(config_path, encoding="utf-8-sig") as f:  # Handle BOM
            return json.load(f)
    except Exception as e:
        print(f"  {ERROR} Error reading {config_path}: {e}")
        return None


def check_npx() -> bool:
    """Check if npx is available."""
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_env_var(var_name: str) -> tuple[bool, str | None]:
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    if value:
        # Show partial value for security
        masked = value[:10] + "..." if len(value) > 10 else value[:len(value)]
        return True, masked
    return False, None


def check_mcp_server(server_name: str, server_config: dict[str, Any]) -> dict[str, Any]:
    """Check status of a single MCP server."""
    status = {
        "name": server_name,
        "configured": True,
        "issues": [],
        "warnings": [],
        "info": [],
    }
    
    # Check command
    command = server_config.get("command", "")
    if command == "npx":
        if not check_npx():
            status["issues"].append("npx not available (required for this server)")
        else:
            status["info"].append("npx is available")
    
    # Check args
    args = server_config.get("args", [])
    if args:
        status["info"].append(f"Command: {command} {' '.join(args)}")
    
    # Check environment variables
    env_vars = server_config.get("env", {})
    for env_name, env_value in env_vars.items():
        if isinstance(env_value, str) and env_value.startswith("${") and env_value.endswith("}"):
            # Environment variable reference
            var_name = env_value[2:-1]  # Remove ${ and }
            is_set, masked_value = check_env_var(var_name)
            if is_set:
                status["info"].append(f"{env_name}: Set (value: {masked_value})")
            else:
                status["issues"].append(
                    f"{env_name}: Environment variable '{var_name}' not set. "
                    f"The MCP server may not work without this."
                )
        else:
            # Direct value (may be a secret, don't show)
            if env_value:
                status["info"].append(f"{env_name}: Set (direct value)")
            else:
                status["warnings"].append(f"{env_name}: Empty or not set")
    
    return status


def main():
    """Main diagnostic function."""
    print("=" * 70)
    print("MCP Tools Diagnostic")
    print("=" * 70)
    print()
    
    # Find config files
    config_files = find_mcp_config_files()
    if not config_files:
        print(f"{ERROR} No MCP configuration files found")
        print()
        print("Expected locations:")
        print("  - .cursor/mcp.json (project-local)")
        print("  - ~/.cursor/mcp.json (user-global)")
        print("  - ~/.config/cursor/mcp.json (user-global)")
        print()
        print("To create a config file, run:")
        print("  tapps-agents init")
        return 1
    
    print(f"{OK} Found {len(config_files)} MCP configuration file(s):")
    for config_file in config_files:
        print(f"  - {config_file}")
    print()
    
    # Load and check each config file
    all_servers: dict[str, dict[str, Any]] = {}
    for config_file in config_files:
        print(f"{FILE} Checking {config_file}:")
        config = load_mcp_config(config_file)
        if not config:
            continue
        
        mcp_servers = config.get("mcpServers", {})
        if not mcp_servers:
            print(f"  {WARNING} No MCP servers configured")
            continue
        
        print(f"  {OK} Found {len(mcp_servers)} MCP server(s)")
        
        # Merge servers (project-local takes precedence)
        for server_name, server_config in mcp_servers.items():
            if server_name not in all_servers or config_file.name == "mcp.json":
                all_servers[server_name] = server_config
    
    if not all_servers:
        print()
        print("❌ No MCP servers found in configuration files")
        return 1
    
    print()
    print("=" * 70)
    print("MCP Server Status")
    print("=" * 70)
    print()
    
    # Check each server
    has_issues = False
    for server_name, server_config in all_servers.items():
        print(f"{TOOL} {server_name}:")
        status = check_mcp_server(server_name, server_config)
        
        if status["info"]:
            for info in status["info"]:
                print(f"  {INFO} {info}")
        
        if status["warnings"]:
            for warning in status["warnings"]:
                print(f"  {WARNING} {warning}")
        
        if status["issues"]:
            has_issues = True
            for issue in status["issues"]:
                print(f"  {ERROR} {issue}")
        
        if not status["issues"] and not status["warnings"]:
            print(f"  {OK} Configuration looks good")
        
        print()
    
    # Summary and recommendations
    print("=" * 70)
    print("Summary & Recommendations")
    print("=" * 70)
    print()
    
    if has_issues:
        print(f"{ERROR} Some issues were found. Recommendations:")
        print()
        
        # Check for Context7 specifically
        if "Context7" in all_servers:
            context7_config = all_servers["Context7"]
            env_vars = context7_config.get("env", {})
            api_key_ref = env_vars.get("CONTEXT7_API_KEY", "")
            
            if isinstance(api_key_ref, str) and api_key_ref.startswith("${"):
                var_name = api_key_ref[2:-1]
                if not os.getenv(var_name):
                    print(f"{TOOL} Fix Context7 Configuration:")
                    print()
                    print("The Context7 MCP server requires CONTEXT7_API_KEY to be set.")
                    print()
                    print("Option 1: Set environment variable (recommended)")
                    print("  PowerShell:")
                    print("    $env:CONTEXT7_API_KEY='your-api-key-here'")
                    print()
                    print("  Bash/Zsh:")
                    print("    export CONTEXT7_API_KEY='your-api-key-here'")
                    print()
                    print("Option 2: Update .cursor/mcp.json with direct value")
                    print("  (Less secure, but works if env var not available)")
                    print("  Replace:")
                    print('    "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"')
                    print("  With:")
                    print('    "CONTEXT7_API_KEY": "your-api-key-here"')
                    print()
                    print("After setting the API key, restart Cursor for changes to take effect.")
                    print()
        
        return 1
    else:
        print(f"{OK} All MCP servers are properly configured!")
        print()
        print("If you're still seeing errors in Cursor:")
        print("  1. Restart Cursor completely")
        print("  2. Check Cursor's MCP server logs (View > Output > MCP)")
        print("  3. Verify your API keys are valid")
        return 0


if __name__ == "__main__":
    sys.exit(main())
