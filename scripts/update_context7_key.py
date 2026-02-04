#!/usr/bin/env python3
"""
Update Context7 API Key Utility.

This script helps update the Context7 API key in encrypted storage.

Usage:
    python scripts/update_context7_key.py --key "your-api-key"
    python scripts/update_context7_key.py --verify       # Verify current key
    python scripts/update_context7_key.py --test         # Test API connection
    python scripts/update_context7_key.py --set-user-env # Set CONTEXT7_API_KEY at User from storage (for Cursor MCP)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

import httpx

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tapps_agents.context7.security import APIKeyManager


def verify_current_key():
    """Verify the currently stored API key."""
    print("=" * 60)
    print("Context7 API Key Verification")
    print("=" * 60)
    print()
    
    key_manager = APIKeyManager()
    api_key = key_manager.load_api_key("context7")
    
    if not api_key:
        print("[ERROR] No API key found in encrypted storage")
        print()
        print("To store an API key, run:")
        print("  python scripts/update_context7_key.py --key 'your-api-key'")
        return False
    
    print(f"[OK] API key found: {api_key[:15]}...{api_key[-5:]}")
    print(f"     Key length: {len(api_key)} characters")
    print()
    
    # Check environment variable
    env_key = os.getenv("CONTEXT7_API_KEY")
    if env_key:
        if env_key == api_key:
            print("[OK] Environment variable matches stored key")
        else:
            print("[WARN] Environment variable differs from stored key")
            print(f"       Env key: {env_key[:15]}...")
    else:
        print("[INFO] CONTEXT7_API_KEY environment variable not set")
        print("       The stored key will be loaded automatically")
    
    return True


def test_api_key(api_key: str | None = None):
    """Test the API key with Context7 API."""
    print("=" * 60)
    print("Context7 API Connection Test")
    print("=" * 60)
    print()
    
    if not api_key:
        key_manager = APIKeyManager()
        api_key = key_manager.load_api_key("context7")
    
    if not api_key:
        print("[ERROR] No API key available to test")
        return False
    
    print(f"Testing key: {api_key[:15]}...")
    print()
    
    API_URL = "https://context7.com/api/v2"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{API_URL}/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                params={"query": "react"},
            )
            
            auth_status = response.headers.get("x-clerk-auth-status", "unknown")
            quota_tier = response.headers.get("context7-quota-tier", "unknown")
            
            print(f"Status Code: {response.status_code}")
            print(f"Auth Status: {auth_status}")
            print(f"Quota Tier:  {quota_tier}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print("[SUCCESS] API connection successful!")
                    print(f"          Found {len(data)} library results")
                    if len(data) > 0:
                        print(f"          First: {data[0].get('id', 'N/A')}")
                return True
            elif response.status_code == 429:
                error_data = response.json()
                message = error_data.get("message", "Quota exceeded")
                print(f"[QUOTA] API quota exceeded: {message}")
                print()
                if quota_tier == "anonymous":
                    print("  NOTE: Quota tier shows 'anonymous' - key may not be authenticated")
                    print("        Check that the key format is correct (starts with 'ctx7sk-')")
                elif quota_tier == "free":
                    print("  NOTE: Key is authenticated but quota is exhausted")
                    print("        Create a new key at https://context7.com/dashboard")
                return False
            else:
                print(f"[ERROR] Unexpected response: {response.status_code}")
                print(f"        {response.text[:200]}")
                return False
                
    except httpx.ConnectError as e:
        print(f"[ERROR] Cannot connect to Context7 API: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False


def update_api_key(new_key: str, *, skip_prompts: bool = False):
    """Update the API key in encrypted storage."""
    print("=" * 60)
    print("Context7 API Key Update")
    print("=" * 60)
    print()

    # Validate key format
    if not new_key.startswith("ctx7sk-"):
        if not skip_prompts:
            print("[WARN] Key doesn't start with 'ctx7sk-' - this may not be a valid Context7 key")
            response = input("Continue anyway? [y/N]: ")
            if response.lower() != "y":
                print("Aborted")
                return False
        else:
            print("[WARN] Key doesn't start with 'ctx7sk-' - storing anyway (--yes)")

    print(f"New key: {new_key[:15]}...{new_key[-5:]}")
    print()

    # Test the new key first
    print("Testing new key...")
    print("-" * 40)
    if not test_api_key(new_key):
        if not skip_prompts:
            print()
            print("[WARN] Key test failed, but this might be due to:")
            print("       - Rate limiting")
            print("       - Temporary API issues")
            print()
            response = input("Store the key anyway? [y/N]: ")
            if response.lower() != "y":
                print("Aborted")
                return False
        else:
            print("[WARN] Key test failed - storing anyway (--yes)")
    print()
    
    # Store the key
    print("Storing key in encrypted storage...")
    key_manager = APIKeyManager()
    key_manager.store_api_key("context7", new_key, encrypt=True)
    print()
    print("[OK] API key stored successfully!")
    print()
    print("The key will be loaded automatically when making Context7 API calls.")
    print()
    print("To also set the environment variable (for this session):")
    print(f'  $env:CONTEXT7_API_KEY="{new_key}"')
    print()
    
    return True


def set_user_env_from_storage() -> bool:
    """
    Load the Context7 key from encrypted storage and set CONTEXT7_API_KEY
    at User level so Cursor's MCP server can use it. The key is passed to
    PowerShell via the subprocess environment (not argv) to avoid logging.
    """
    key_manager = APIKeyManager()
    api_key = key_manager.load_api_key("context7")
    if not api_key:
        print("[ERROR] No API key found in encrypted storage.")
        print("        Run: python scripts/update_context7_key.py --key 'your-api-key'")
        return False

    if sys.platform == "win32":
        ps = (
            "$k = [System.Environment]::GetEnvironmentVariable('CTX7_FROM_SCRIPT','Process');"
            "[System.Environment]::SetEnvironmentVariable('CONTEXT7_API_KEY', $k, 'User');"
            "Write-Host '[OK] CONTEXT7_API_KEY set at User level from encrypted storage.'"
        )
        env = {**os.environ, "CTX7_FROM_SCRIPT": api_key}
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0:
                print(r.stdout or "[OK] CONTEXT7_API_KEY set at User level from encrypted storage.")
                print()
                print("Next: fully quit Cursor (File > Exit) and reopen so it picks up the variable.")
                return True
            print(f"[ERROR] PowerShell: {r.stderr or r.stdout or 'unknown'}")
            return False
        except Exception as e:
            print(f"[ERROR] {e}")
            return False
    else:
        print("[OK] Key found in encrypted storage.")
        print("      Set for your shell:  export CONTEXT7_API_KEY='<your-key>'")
        print("      For persistence add that to ~/.bashrc or ~/.zshrc")
        print("      (Key not printed here; use --verify to confirm it exists.)")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Update Context7 API Key",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Store a new API key
    python scripts/update_context7_key.py --key "ctx7sk-xxxx-xxxx"
    
    # Verify the current key
    python scripts/update_context7_key.py --verify
    
    # Test API connection
    python scripts/update_context7_key.py --test

    # Set CONTEXT7_API_KEY at User level from encrypted storage (for Cursor MCP)
    python scripts/update_context7_key.py --set-user-env
"""
    )
    
    parser.add_argument("--key", "-k", help="New API key to store")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip prompts when storing (store even if test fails)")
    parser.add_argument("--verify", "-v", action="store_true", help="Verify current key")
    parser.add_argument("--test", "-t", action="store_true", help="Test API connection")
    parser.add_argument("--set-user-env", action="store_true",
                        help="Set CONTEXT7_API_KEY at User level from encrypted storage (for Cursor MCP)")
    
    args = parser.parse_args()
    
    if args.set_user_env:
        sys.exit(0 if set_user_env_from_storage() else 1)
    if args.verify:
        verify_current_key()
    elif args.test:
        test_api_key()
    elif args.key:
        update_api_key(args.key, skip_prompts=args.yes)
    else:
        # Default: verify and test
        if verify_current_key():
            print()
            test_api_key()


if __name__ == "__main__":
    main()
