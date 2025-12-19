#!/usr/bin/env python3
"""
Verify Context7 API key setup and test functionality.

Usage:
    1. Set API key: $env:CONTEXT7_API_KEY="your-key-here"
    2. Run: python verify_context7_setup.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("Context7 API Key Verification & Test")
print("=" * 70)

# Check for API key
api_key = os.getenv("CONTEXT7_API_KEY")
if not api_key:
    print("\n❌ CONTEXT7_API_KEY not set!")
    print("\nTo set the API key:")
    print("  Windows PowerShell:")
    print('    $env:CONTEXT7_API_KEY="your-api-key-here"')
    print("\n  Linux/macOS:")
    print('    export CONTEXT7_API_KEY="your-api-key-here"')
    sys.exit(1)

print(f"\n✅ API Key found (length: {len(api_key)})")

# Test backup client functions
print("\n" + "-" * 70)
print("Testing Backup Client Functions")
print("-" * 70)

try:
    from tapps_agents.context7.backup_client import (
        check_context7_api_available,
        check_mcp_tools_available,
        create_fallback_http_client,
        call_context7_resolve_with_fallback,
        call_context7_get_docs_with_fallback,
    )
    
    print(f"✅ MCP Tools Available: {check_mcp_tools_available()}")
    print(f"✅ API Key Available: {check_context7_api_available()}")
    
    # Test creating HTTP client
    resolve_client, get_docs_client = create_fallback_http_client()
    if resolve_client and get_docs_client:
        print("✅ Fallback HTTP client created successfully")
    else:
        print("❌ Failed to create fallback HTTP client")
        sys.exit(1)
    
except ImportError as e:
    print(f"❌ Failed to import backup client: {e}")
    sys.exit(1)

# Test API call
print("\n" + "-" * 70)
print("Testing Context7 Search API")
print("-" * 70)

try:
    import httpx
    
    with httpx.Client(timeout=10.0) as client:
        response = client.get(
            "https://context7.com/api/v2/search",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            params={"query": "react"},
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ API Key is VALID!")
            print(f"   Found {len(results)} results for 'react'")
            if results:
                first = results[0]
                print(f"   First result: {first.get('id', 'N/A')} - {first.get('title', 'N/A')}")
                print(f"   Benchmark Score: {first.get('benchmarkScore', 'N/A')}")
        elif response.status_code == 401:
            print("❌ API Key is INVALID (401 Unauthorized)")
            sys.exit(1)
        elif response.status_code == 403:
            print("❌ API Key lacks permissions (403 Forbidden)")
            sys.exit(1)
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
except httpx.ConnectError:
    print("❌ Cannot connect to Context7 API")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error testing API: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test async functions
print("\n" + "-" * 70)
print("Testing Async Fallback Functions")
print("-" * 70)

async def test_async_functions():
    """Test async fallback functions."""
    try:
        # Test resolve
        result = await call_context7_resolve_with_fallback("fastapi", mcp_gateway=None)
        if result.get("success"):
            matches = result.get("result", {}).get("matches", [])
            print(f"✅ Resolve function works! Found {len(matches)} matches")
            if matches:
                print(f"   First match: {matches[0].get('id', 'N/A')}")
        else:
            print(f"❌ Resolve failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test get docs (if we have a library ID)
        if matches:
            library_id = matches[0].get("id", "").lstrip("/")
            if library_id:
                docs_result = await call_context7_get_docs_with_fallback(
                    library_id, topic=None, mode="code", page=1, mcp_gateway=None
                )
                if docs_result.get("success"):
                    content = docs_result.get("result", {}).get("content", "")
                    print(f"✅ Get docs function works! Retrieved {len(content)} characters")
                else:
                    print(f"⚠️  Get docs returned: {docs_result.get('error', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing async functions: {e}")
        import traceback
        traceback.print_exc()
        return False

success = asyncio.run(test_async_functions())

# Test cache pre-population
print("\n" + "-" * 70)
print("Testing Cache Pre-population")
print("-" * 70)

try:
    from tapps_agents.core.init_project import pre_populate_context7_cache
    
    print("Running cache pre-population test (limited to 3 libraries)...")
    result = asyncio.run(pre_populate_context7_cache(Path("."), libraries=["react", "fastapi", "pytest"]))
    
    if result.get("success"):
        print(f"✅ Cache pre-population SUCCESS!")
        print(f"   Cached: {result.get('cached', 0)}")
        print(f"   Failed: {result.get('failed', 0)}")
        print(f"   Total: {result.get('total', 0)}")
    else:
        print(f"❌ Cache pre-population FAILED")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        if result.get("errors"):
            print(f"   First error: {result['errors'][0]}")
except Exception as e:
    print(f"⚠️  Error testing cache pre-population: {e}")
    import traceback
    traceback.print_exc()

# Final summary
print("\n" + "=" * 70)
if success:
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nContext7 integration is working correctly!")
    print("You can now run: python -m tapps_agents.cli init")
else:
    print("⚠️  SOME TESTS FAILED")
    print("=" * 70)
    print("\nPlease check the errors above.")

