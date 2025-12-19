#!/usr/bin/env python3
"""
Quick script to check where your Context7 API key is stored.

Usage:
    python docs/scripts/check_context7_key.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Context7 API Key Location Check")
print("=" * 70)
print()

# Check 1: Environment Variable
env_key = os.getenv("CONTEXT7_API_KEY")
print(f"1. Environment Variable (CONTEXT7_API_KEY):")
print(f"   Status: {'[SET]' if env_key else '[NOT SET]'}")
if env_key:
    print(f"   Key length: {len(env_key)}")
    print(f"   Key prefix: {env_key[:20]}...")
    print(f"   Priority: HIGHEST (checked first)")
print()

# Check 2: Encrypted Storage
print(f"2. Encrypted Storage (.tapps-agents/api-keys.encrypted):")
try:
    from tapps_agents.context7.security import APIKeyManager
    
    mgr = APIKeyManager()
    encrypted_key = mgr.load_api_key("context7")
    print(f"   Status: {'[FOUND]' if encrypted_key else '[NOT FOUND]'}")
    if encrypted_key:
        print(f"   Key length: {len(encrypted_key)}")
        print(f"   Key prefix: {encrypted_key[:20]}...")
        encrypted_file = project_root / ".tapps-agents" / "api-keys.encrypted"
        if encrypted_file.exists():
            print(f"   File path: {encrypted_file.absolute()}")
            print(f"   File size: {encrypted_file.stat().st_size} bytes")
        print(f"   Priority: FALLBACK (used if environment variable not set)")
except ImportError:
    print(f"   Status: [WARNING] Module not available (cryptography package may be missing)")
except Exception as e:
    print(f"   Status: [ERROR] - {e}")

print()

# Check 3: File Exists
encrypted_file = project_root / ".tapps-agents" / "api-keys.encrypted"
print(f"3. Encrypted File Exists:")
print(f"   Status: {'[YES]' if encrypted_file.exists() else '[NO]'}")
if encrypted_file.exists():
    print(f"   File path: {encrypted_file.absolute()}")
    print(f"   File size: {encrypted_file.stat().st_size} bytes")
    try:
        from datetime import datetime
        mtime = datetime.fromtimestamp(encrypted_file.stat().st_mtime)
        print(f"   Last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception:
        pass

print()

# Summary
final_key = env_key or encrypted_key
print("=" * 70)
print("SUMMARY")
print("=" * 70)
if final_key:
    print(f"[OK] API KEY AVAILABLE")
    if env_key:
        print(f"   Source: Environment Variable (CONTEXT7_API_KEY)")
        print(f"   Action: Key is ready to use")
    elif encrypted_key:
        print(f"   Source: Encrypted Storage")
        print(f"   Action: Key is available but not in environment")
        print(f"   To use: Load it to environment variable:")
        print(f"     Windows: $env:CONTEXT7_API_KEY = (python -c \"from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')\")")
        print(f"     Linux/Mac: export CONTEXT7_API_KEY=$(python -c \"from tapps_agents.context7.security import APIKeyManager; mgr = APIKeyManager(); key = mgr.load_api_key('context7'); print(key if key else '')\")")
else:
    print(f"[FAILED] NO API KEY FOUND")
    print(f"   Action: Set CONTEXT7_API_KEY environment variable or store in encrypted storage")
    print(f"   See: docs/CONTEXT7_API_KEY_MANAGEMENT.md for instructions")

print("=" * 70)

