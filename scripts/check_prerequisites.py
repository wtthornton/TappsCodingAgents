#!/usr/bin/env python3
"""
Pre-installation prerequisite check for TappsCodingAgents.

Verifies Python 3.13+ is available. On Windows, checks for 'py -3.13'.
Run before: pip install -e .  or  pip install tapps-agents

Usage:
  python scripts/check_prerequisites.py

Exit: 0 if OK, 1 if Python 3.13+ not available.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _check_py_313_windows() -> tuple[bool, str | None]:
    """On Windows, try 'py -3.13 --version'. Return (found, version_or_error)."""
    if sys.platform != "win32":
        return False, None
    try:
        out = subprocess.run(
            ["py", "-3.13", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8",
            errors="replace",
        )
        if out.returncode == 0 and out.stdout:
            return True, (out.stdout.strip() or "3.13")
        return False, "py -3.13 did not return a version"
    except FileNotFoundError:
        return False, "py launcher not found"
    except subprocess.TimeoutExpired:
        return False, "py -3.13 timed out"
    except Exception as e:
        return False, str(e)


def main() -> int:
    cur = sys.version_info
    if cur >= (3, 13):
        v = f"{cur.major}.{cur.minor}.{cur.micro}"
        try:
            print(f"[OK] Python {v}")
        except UnicodeEncodeError:
            print(f"[OK] Python {v}")
        return 0

    # Not 3.13+
    try:
        print("[FAIL] Python 3.13+ required")
        print(f"  Required: Python 3.13+")
        print(f"  Detected: Python {cur.major}.{cur.minor}.{cur.micro}")
        print("")
        print("Solutions:")
        print("  1. Install Python 3.13+ from https://www.python.org/downloads/")
        print("  2. Windows: py -3.13 -m pip install -e .")
        print("  3. Linux/macOS: python3.13 -m pip install -e .")
        print("")
    except UnicodeEncodeError:
        print("[FAIL] Python 3.13+ required")
        print("  Install from https://www.python.org/downloads/")
        print("  Windows: py -3.13 -m pip install -e .")

    if sys.platform == "win32":
        found, msg = _check_py_313_windows()
        if found:
            try:
                print("Checking for Python 3.13 via py launcher...")
                print("[OK] Found. Use: py -3.13 -m pip install -e .")
            except UnicodeEncodeError:
                print("Found. Use: py -3.13 -m pip install -e .")
        elif msg:
            try:
                print("Checking for Python 3.13 via py launcher...")
                print(f"  (py -3.13: {msg})")
            except UnicodeEncodeError:
                pass

    return 1


if __name__ == "__main__":
    sys.exit(main())
