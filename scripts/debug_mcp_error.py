#!/usr/bin/env python3
"""
Debug MCP Server Error - Systematic diagnosis

This script systematically checks all potential causes of MCP server errors
and logs detailed diagnostic information.
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

LOG_PATH = Path(".cursor/debug.log")

def log_debug(hypothesis_id: str, location: str, message: str, data: dict):
    """Write debug log entry."""
    import time
    log_entry = {
        "id": f"log_{int(time.time() * 1000)}",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": hypothesis_id
    }
    try:
        # Ensure log directory exists
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass


def main():
    """Main diagnostic function."""
    project_root = Path.cwd()
    mcp_file = project_root / ".cursor" / "mcp.json"
    
    print("=" * 70)
    print("MCP Server Error Diagnostic")
    print("=" * 70)
    print()
    
    # Hypothesis A: Config file not found or invalid JSON
    log_debug("A", "debug_mcp_error.py:main", "Checking config file existence", {
        "mcp_file": str(mcp_file),
        "exists": mcp_file.exists()
    })
    
    if not mcp_file.exists():
        print(f"[ERROR] MCP config not found: {mcp_file}")
        return 1
    
    # Hypothesis B: JSON syntax error
    log_debug("B", "debug_mcp_error.py:main", "Parsing JSON config", {
        "file": str(mcp_file)
    })
    
    try:
        with open(mcp_file, encoding="utf-8-sig") as f:
            config = json.load(f)
        log_debug("B", "debug_mcp_error.py:main", "JSON parsed successfully", {
            "has_mcpServers": "mcpServers" in config,
            "server_count": len(config.get("mcpServers", {}))
        })
    except json.JSONDecodeError as e:
        log_debug("B", "debug_mcp_error.py:main", "JSON parse error", {
            "error": str(e),
            "line": getattr(e, "lineno", None),
            "col": getattr(e, "colno", None)
        })
        print(f"[ERROR] Invalid JSON: {e}")
        return 1
    except Exception as e:
        log_debug("B", "debug_mcp_error.py:main", "File read error", {"error": str(e)})
        print(f"[ERROR] Failed to read config: {e}")
        return 1
    
    mcp_servers = config.get("mcpServers", {})
    
    if "Context7" not in mcp_servers:
        print("[ERROR] Context7 server not found in config")
        return 1
    
    context7_config = mcp_servers["Context7"]
    
    # Hypothesis C: API key missing or invalid format
    log_debug("C", "debug_mcp_error.py:main", "Checking Context7 API key", {
        "has_env": "env" in context7_config,
        "has_key": "env" in context7_config and "CONTEXT7_API_KEY" in context7_config["env"]
    })
    
    env_vars = context7_config.get("env", {})
    api_key = env_vars.get("CONTEXT7_API_KEY", "")
    
    log_debug("C", "debug_mcp_error.py:main", "API key details", {
        "key_length": len(api_key) if api_key else 0,
        "is_placeholder": api_key.startswith("${") if api_key and len(api_key) > 0 else False,
        "key_prefix": api_key[:10] if api_key and len(api_key) > 10 else (api_key if api_key else "")
    })
    
    if not api_key:
        print("[ERROR] CONTEXT7_API_KEY not found in config")
        return 1
    
    if api_key.startswith("${"):
        print(f"[WARN] API key is a placeholder: {api_key}")
        print("       This may not work if Cursor doesn't support env var substitution")
    
    # Hypothesis D: npx not available
    log_debug("D", "debug_mcp_error.py:main", "Checking npx availability", {})
    
    # Find npx executable (handles Windows PATH issues)
    npx_path = shutil.which("npx")
    if not npx_path:
        # Try common Windows locations
        common_paths = [
            r"C:\Program Files\nodejs\npx.cmd",
            r"C:\Program Files (x86)\nodejs\npx.cmd",
        ]
        for path in common_paths:
            if os.path.exists(path):
                npx_path = path
                break
    
    log_debug("D", "debug_mcp_error.py:main", "npx path resolution", {
        "found": npx_path is not None,
        "path": npx_path
    })
    
    if not npx_path:
        log_debug("D", "debug_mcp_error.py:main", "npx not found", {})
        print("[ERROR] npx not found (Node.js not installed or not in PATH?)")
        print("       Try: where npx  (to find npx location)")
        print("       Or install Node.js from https://nodejs.org/")
        return 1
    
    try:
        # Use shell=True on Windows to ensure PATH is respected
        use_shell = sys.platform == "win32"
        result = subprocess.run(
            [npx_path, "--version"] if not use_shell else f'"{npx_path}" --version',
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            shell=use_shell
        )
        npx_available = result.returncode == 0
        log_debug("D", "debug_mcp_error.py:main", "npx check result", {
            "available": npx_available,
            "version": result.stdout.strip() if npx_available else None,
            "error": result.stderr.strip() if not npx_available else None
        })
        
        if not npx_available:
            print(f"[ERROR] npx not available: {result.stderr}")
            return 1
        print(f"[OK] npx available: {result.stdout.strip()}")
    except FileNotFoundError:
        log_debug("D", "debug_mcp_error.py:main", "npx not found", {})
        print("[ERROR] npx not found (Node.js not installed?)")
        return 1
    except Exception as e:
        log_debug("D", "debug_mcp_error.py:main", "npx check exception", {"error": str(e)})
        print(f"[ERROR] Failed to check npx: {e}")
        return 1
    
    # Hypothesis E: Package not found or wrong package name
    log_debug("E", "debug_mcp_error.py:main", "Checking package name", {
        "command": context7_config.get("command"),
        "args": context7_config.get("args", [])
    })
    
    package_name = None
    args = context7_config.get("args", [])
    if args and len(args) > 0:
        # Look for package name in args (usually last arg)
        for arg in reversed(args):
            if arg.startswith("@") or "/" in arg:
                package_name = arg
                break
    
    log_debug("E", "debug_mcp_error.py:main", "Package details", {
        "package_name": package_name,
        "args": args
    })
    
    if package_name:
        print(f"[INFO] Testing package: {package_name}")
        # Try to check if package exists (this may take time, so use timeout)
        try:
            # Use npx_path if we found it, otherwise try "npx"
            npx_cmd = npx_path if npx_path else "npx"
            use_shell = sys.platform == "win32"
            cmd = [npx_cmd, "-y", package_name, "--help"] if not use_shell else f'"{npx_cmd}" -y {package_name} --help'
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                shell=use_shell
            )
            log_debug("E", "debug_mcp_error.py:main", "Package test result", {
                "package": package_name,
                "exit_code": result.returncode,
                "stdout_length": len(result.stdout),
                "stderr_length": len(result.stderr),
                "stderr_preview": result.stderr[:200] if result.stderr else None
            })
            
            if result.returncode != 0:
                print(f"[WARN] Package test failed (exit code {result.returncode})")
                print(f"       stderr: {result.stderr[:200]}")
            else:
                print(f"[OK] Package {package_name} is accessible")
        except subprocess.TimeoutExpired:
            log_debug("E", "debug_mcp_error.py:main", "Package test timeout", {
                "package": package_name
            })
            print("[WARN] Package test timed out (may still be valid)")
        except Exception as e:
            log_debug("E", "debug_mcp_error.py:main", "Package test exception", {
                "package": package_name,
                "error": str(e)
            })
            print(f"[WARN] Failed to test package: {e}")
    
    # Hypothesis F: Config structure issues
    log_debug("F", "debug_mcp_error.py:main", "Validating config structure", {
        "has_command": "command" in context7_config,
        "has_args": "args" in context7_config,
        "command": context7_config.get("command"),
        "args_count": len(context7_config.get("args", []))
    })
    
    required_fields = ["command", "args"]
    missing_fields = [f for f in required_fields if f not in context7_config]
    if missing_fields:
        log_debug("F", "debug_mcp_error.py:main", "Missing required fields", {
            "missing": missing_fields
        })
        print(f"[ERROR] Missing required fields: {missing_fields}")
        return 1
    
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Config file: {mcp_file}")
    print("JSON valid: Yes")
    print("Context7 configured: Yes")
    print(f"API key present: {'Yes' if api_key else 'No'}")
    print(f"API key format: {'Placeholder' if api_key and api_key.startswith('${') else 'Direct value'}")
    print("npx available: Yes")
    print(f"Package: {package_name or 'Unknown'}")
    print()
    print("Check Cursor's MCP output panel for detailed error messages:")
    print("  1. Open Output panel (Ctrl+Shift+U)")
    print("  2. Select 'MCP' from dropdown")
    print("  3. Look for Context7 error messages")
    print()
    print("Debug logs written to: .cursor/debug.log")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
