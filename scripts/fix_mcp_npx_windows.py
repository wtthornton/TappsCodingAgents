#!/usr/bin/env python3
"""
Fix MCP npx Configuration for Windows - 2025 Solution

This script fixes the common "npx not working" issue in Cursor MCP configuration
on Windows by replacing npx commands with full paths to Node.js and the package.

Based on 2025 troubleshooting guides:
- https://akmaster.github.io/context7-mcp-troubleshooting/troubleshooting-guide/
- https://forum.cursor.com/t/mcp-setup-on-windows-fix-npx-problem/92830
"""

import json
import os
import shutil
import subprocess
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


def find_node_path() -> str | None:
    """Find Node.js executable path."""
    node_path = shutil.which("node")
    if node_path:
        return node_path
    
    # Try common Windows locations
    common_paths = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None


def find_npm_global_modules() -> Path | None:
    """Find npm global modules directory."""
    try:
        result = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            shell=sys.platform == "win32"
        )
        if result.returncode == 0:
            path_str = result.stdout.strip()
            if path_str:
                path = Path(path_str)
                if path.exists():
                    return path
    except Exception as e:
        print(f"[DEBUG] npm root -g failed: {e}")
    
    # Try common locations
    username = os.environ.get("USERNAME") or os.environ.get("USER", "")
    if username:
        common_paths = [
            Path(f"C:\\Users\\{username}\\AppData\\Roaming\\npm\\node_modules"),
            Path(f"C:\\Users\\{username}\\AppData\\Local\\npm\\node_modules"),
        ]
        for path in common_paths:
            if path.exists():
                return path
    
    # Try without username (fallback)
    common_paths = [
        Path(r"C:\Users\Public\npm\node_modules"),
    ]
    for path in common_paths:
        if path.exists():
            return path
    
    return None


def install_context7_package(global_modules: Path) -> Path | None:
    """Install @context7/mcp-server globally and return path."""
    print("[INFO] Installing @context7/mcp-server globally...")
    try:
        result = subprocess.run(
            ["npm", "install", "-g", "@context7/mcp-server@latest"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120
        )
        if result.returncode == 0:
            package_path = global_modules / "@context7" / "mcp-server"
            if package_path.exists():
                # Find the entry point (usually dist/index.js or index.js)
                entry_points = [
                    package_path / "dist" / "index.js",
                    package_path / "index.js",
                    package_path / "src" / "index.js",
                ]
                for entry in entry_points:
                    if entry.exists():
                        return entry
                # Return package directory if no entry point found
                return package_path
            print(f"[WARN] Package installed but path not found: {package_path}")
        else:
            print(f"[WARN] Installation failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"[WARN] Failed to install package: {e}")
    
    return None


def fix_mcp_config(mcp_file: Path, use_full_paths: bool = True) -> bool:
    """Fix MCP config by replacing npx with full paths."""
    try:
        # Read config
        with open(mcp_file, encoding="utf-8-sig") as f:
            config = json.load(f)
        
        mcp_servers = config.get("mcpServers", {})
        updated = False
        
        # Fix all servers that use npx
        servers_to_fix = []
        if "Context7" in mcp_servers:
            servers_to_fix.append(("Context7", mcp_servers["Context7"]))
        if "GitHub" in mcp_servers:
            servers_to_fix.append(("GitHub", mcp_servers["GitHub"]))
        
        for server_name, server_config in servers_to_fix:
            if server_config.get("command") in ["npx", "npx.cmd", "npx.CMD"]:
                print(f"[INFO] Fixing {server_name} configuration...")
                
                if use_full_paths:
                    # Solution 1: Use full paths (recommended for 2025)
                    node_path = find_node_path()
                    if not node_path:
                        print("[ERROR] Node.js not found. Please install Node.js from https://nodejs.org/")
                        return False
                    
                    # Solution 1: Try using npx.cmd with full path (2025 Windows fix)
                    npx_cmd_path = shutil.which("npx")
                    if not npx_cmd_path:
                        # Try common locations - check actual file name case
                        for base_path in [
                            r"C:\Program Files\nodejs",
                            r"C:\Program Files (x86)\nodejs",
                        ]:
                            if os.path.exists(base_path):
                                # Check for npx.cmd (case-insensitive search)
                                for file in os.listdir(base_path):
                                    if file.lower() == "npx.cmd":
                                        npx_cmd_path = os.path.join(base_path, file)
                                        break
                                if npx_cmd_path:
                                    break
                    
                    if npx_cmd_path and os.path.exists(npx_cmd_path):
                        server_config["command"] = npx_cmd_path
                        # Keep original args
                        updated = True
                        print(f"[OK] Updated {server_name} to use full npx path: {npx_cmd_path}")
                        print("       This fixes the PATH issue in Cursor's child process")
                    else:
                        # Solution 2: Try installing package globally and using direct node path
                        global_modules = find_npm_global_modules()
                        if global_modules:
                            package_entry = global_modules / "@context7" / "mcp-server"
                            entry_point = None
                            
                            if package_entry.exists():
                                # Find entry point
                                for entry in [
                                    package_entry / "dist" / "index.js",
                                    package_entry / "index.js",
                                    package_entry / "src" / "index.js",
                                ]:
                                    if entry.exists():
                                        entry_point = entry
                                        break
                            else:
                                # Install the package
                                entry_point = install_context7_package(global_modules)
                            
                            if entry_point and entry_point.exists():
                                server_config["command"] = node_path
                                server_config["args"] = [str(entry_point)]
                                updated = True
                                print(f"[OK] Updated {server_name} to use: {node_path} {entry_point}")
                            else:
                                print("[ERROR] Could not find or install @context7/mcp-server")
                                print("       Try manually: npm install -g @context7/mcp-server")
                                return False
                        else:
                            print("[ERROR] npm global modules directory not found")
                            print("       And npx.cmd not found at expected location")
                            return False
                else:
                    # Solution 2: Use URL-based config (if supported)
                    # This is a newer approach mentioned in some guides
                    print("[INFO] URL-based config not yet implemented, using full paths...")
                    return fix_mcp_config(mcp_file, use_full_paths=True)
        
        if updated:
            # Write back
            with open(mcp_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
                f.write("\n")
            print(f"[OK] MCP config updated: {mcp_file}")
            return True
        else:
            print("[INFO] No changes needed (servers not using npx or already fixed)")
            return True
            
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in MCP config: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to fix config: {e}")
        return False


def main():
    """Main function."""
    print("=" * 70)
    print("Fix MCP npx Configuration for Windows (2025 Solution)")
    print("=" * 70)
    print()
    
    project_root = Path.cwd()
    mcp_file = project_root / ".cursor" / "mcp.json"
    
    if not mcp_file.exists():
        print(f"[ERROR] MCP config not found: {mcp_file}")
        print("       Run 'tapps-agents init' to create it")
        return 1
    
    print(f"[INFO] Found MCP config: {mcp_file}")
    print()
    
    # Create backup
    backup_file = mcp_file.with_suffix(".json.backup")
    try:
        import shutil
        shutil.copy2(mcp_file, backup_file)
        print(f"[INFO] Backup created: {backup_file}")
    except Exception as e:
        print(f"[WARN] Failed to create backup: {e}")
    
    print()
    
    # Fix config
    if fix_mcp_config(mcp_file):
        print()
        print("=" * 70)
        print("Fix Complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Restart Cursor IDE completely")
        print("2. Check MCP server status in Settings > Tools & MCP")
        print("3. If still not working, check Cursor's MCP output panel:")
        print("   - Open Output panel (Ctrl+Shift+U)")
        print("   - Select 'MCP' from dropdown")
        print("   - Look for Context7 error messages")
        print()
        print(f"Backup saved to: {backup_file}")
        return 0
    else:
        print()
        print("[ERROR] Failed to fix configuration")
        print("       Restore backup if needed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
