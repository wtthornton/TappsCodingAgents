"""
Test script to make 2 Context7 API calls to verify account connection.
This will show up in your Context7 dashboard as 2 requests.
"""

import asyncio
import os
import sys
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass  # Python < 3.7

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Reset quota state for fresh test
import tapps_agents.context7.backup_client as bc_module
from tapps_agents.context7.backup_client import (
    call_context7_resolve_with_fallback,
    is_context7_quota_exceeded,
)

bc_module._CONTEXT7_QUOTA_EXCEEDED = False
bc_module._CONTEXT7_QUOTA_MESSAGE = None

# Reset circuit breaker
from tapps_agents.context7.circuit_breaker import get_context7_circuit_breaker

cb = get_context7_circuit_breaker()
cb.reset()
from tapps_agents.mcp.gateway import MCPGateway


async def make_test_calls():
    """Make 2 Context7 API calls to verify account connection."""
    print("=" * 60)
    print("Context7 Account Verification")
    print("Making 2 API calls to verify account connection...")
    print("=" * 60)
    
    # Check if quota is already exceeded (but allow test calls anyway)
    if is_context7_quota_exceeded():
        print("⚠️  WARNING: Context7 quota marked as exceeded in code state")
        print("   Resetting for test - making actual API calls...")
        # Reset for test - force reset
        bc_module._CONTEXT7_QUOTA_EXCEEDED = False
        bc_module._CONTEXT7_QUOTA_MESSAGE = None
        cb.reset()
        
    # Force bypass quota check for test (comment out fast-fail checks in backup_client)
    # We'll patch the resolve function temporarily
    print("   API key loaded, making calls directly to Context7 API...")
    
    try:
        # Initialize MCP Gateway (may be None if not available)
        try:
            mcp_gateway = MCPGateway()
        except Exception:
            mcp_gateway = None
            print("⚠️  MCP Gateway not available, using HTTP fallback")
        
        # Call 1: Resolve library ID for "fastapi"
        print("\n📞 Call 1: Resolving library ID for 'fastapi'...")
        try:
            resolve_result = await call_context7_resolve_with_fallback(
                "fastapi",
                mcp_gateway=mcp_gateway
            )
            
            if resolve_result.get("success"):
                matches = resolve_result.get("result", {}).get("matches", [])
                if matches:
                    match = matches[0]
                    lib_id = match.get("id") or match.get("library_id")
                    print("✅ Call 1 SUCCESS")
                    print("   Library: fastapi")
                    print(f"   Context7 ID: {lib_id}")
                    print(f"   Title: {match.get('title', 'N/A')}")
                else:
                    print("✅ Call 1 SUCCESS (no matches found)")
            else:
                error = resolve_result.get("error", "Unknown error")
                print(f"❌ Call 1 FAILED: {error}")
                
        except Exception as e:
            print(f"❌ Call 1 ERROR: {e}")
        
        # Call 2: Resolve library ID for "react" (simpler, more reliable)
        print("\n📞 Call 2: Resolving library ID for 'react'...")
        try:
            resolve_result2 = await call_context7_resolve_with_fallback(
                "react",
                mcp_gateway=mcp_gateway
            )
            
            if resolve_result2.get("success"):
                matches = resolve_result2.get("result", {}).get("matches", [])
                if matches:
                    match = matches[0]
                    lib_id = match.get("id") or match.get("library_id")
                    print("✅ Call 2 SUCCESS")
                    print("   Library: react")
                    print(f"   Context7 ID: {lib_id}")
                    print(f"   Title: {match.get('title', 'N/A')}")
                else:
                    print("✅ Call 2 SUCCESS (no matches found)")
            else:
                error = resolve_result2.get("error", "Unknown error")
                print(f"❌ Call 2 FAILED: {error}")
                
        except Exception as e:
            print(f"❌ Call 2 ERROR: {e}")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("   Check your Context7 dashboard to verify:")
    print("   - REQUESTS should show 2/500 (or more if other calls were made)")
    print("   - LAST USED should update to 'Just now' or '1 minute ago'")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(make_test_calls())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
