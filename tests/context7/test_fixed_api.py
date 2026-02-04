"""Test the fixed Context7 API authentication."""

import asyncio
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except:
        pass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Reset quota state before testing
from tapps_agents.context7 import backup_client as bc

bc._CONTEXT7_QUOTA_EXCEEDED = False
bc._CONTEXT7_QUOTA_MESSAGE = None

from tapps_agents.context7.circuit_breaker import get_context7_circuit_breaker

get_context7_circuit_breaker().reset()

from tapps_agents.context7.backup_client import call_context7_resolve_with_fallback


async def test_fixed_api():
    print("=" * 60)
    print("Testing FIXED Context7 API Call")
    print("(Using X-API-Key header instead of Bearer token)")
    print("=" * 60)
    
    # Test 1: Resolve library
    print("\nCall 1: Resolving 'fastapi'...")
    result1 = await call_context7_resolve_with_fallback("fastapi")
    
    if result1.get("success"):
        matches = result1.get("result", {}).get("matches", [])
        print(f"SUCCESS! Found {len(matches)} matches")
        if matches:
            first = matches[0]
            print(f"  First match: {first.get('title')} (ID: {first.get('id')})")
    else:
        print(f"FAILED: {result1.get('error')}")
    
    # Test 2: Resolve another library
    print("\nCall 2: Resolving 'react'...")
    result2 = await call_context7_resolve_with_fallback("react")
    
    if result2.get("success"):
        matches = result2.get("result", {}).get("matches", [])
        print(f"SUCCESS! Found {len(matches)} matches")
        if matches:
            first = matches[0]
            print(f"  First match: {first.get('title')} (ID: {first.get('id')})")
    else:
        print(f"FAILED: {result2.get('error')}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("Check your Context7 dashboard:")
    print("  - REQUESTS should now show 2/500")
    print("  - TappsCodingAgents key LAST USED should update")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fixed_api())
