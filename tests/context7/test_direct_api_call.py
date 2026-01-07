"""
Direct API call test - bypasses all quota checks to make actual API calls.
"""

import sys
import os
import asyncio
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import httpx


async def make_direct_api_calls():
    """Make direct HTTP calls to Context7 API, bypassing all quota checks."""
    print("=" * 60)
    print("Direct Context7 API Call Test")
    print("Bypassing all quota checks to make actual API calls...")
    print("=" * 60)
    
    # Load API key directly
    from tapps_agents.context7.backup_client import _ensure_context7_api_key
    api_key = _ensure_context7_api_key()
    
    if not api_key:
        print("❌ ERROR: No API key found!")
        return
    
    print(f"\n✅ API Key loaded: {api_key[:12]}...{api_key[-4:]}")
    print(f"   Full key: {api_key}")
    
    BASE_URL = os.getenv("CONTEXT7_API_URL", "https://context7.com/api/v2")
    
    # Call 1: Resolve library ID for "fastapi"
    print("\n📞 Call 1: Resolving library ID for 'fastapi'...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                params={"query": "fastapi"},
            )
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                results = data if isinstance(data, list) else data.get("results", [])
                if results:
                    match = results[0]
                    print(f"✅ Call 1 SUCCESS")
                    print(f"   Library: fastapi")
                    print(f"   Context7 ID: {match.get('id', 'N/A')}")
                    print(f"   Title: {match.get('title', 'N/A')}")
                else:
                    print(f"✅ Call 1 SUCCESS (no matches found)")
                    print(f"   Response: {data}")
            elif response.status_code == 429:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", "Quota exceeded")
                print(f"❌ Call 1 FAILED: HTTP 429 - {error_msg}")
                print(f"   Response body: {response.text[:200]}")
            else:
                print(f"❌ Call 1 FAILED: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Call 1 ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Call 2: Resolve library ID for "react"
    print("\n📞 Call 2: Resolving library ID for 'react'...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{BASE_URL}/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                params={"query": "react"},
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data if isinstance(data, list) else data.get("results", [])
                if results:
                    match = results[0]
                    print(f"✅ Call 2 SUCCESS")
                    print(f"   Library: react")
                    print(f"   Context7 ID: {match.get('id', 'N/A')}")
                    print(f"   Title: {match.get('title', 'N/A')}")
                else:
                    print(f"✅ Call 2 SUCCESS (no matches found)")
            elif response.status_code == 429:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", "Quota exceeded")
                print(f"❌ Call 2 FAILED: HTTP 429 - {error_msg}")
            else:
                print(f"❌ Call 2 FAILED: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
    except Exception as e:
        print(f"❌ Call 2 ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("   Check your Context7 dashboard:")
    print("   - REQUESTS should show 2/500 (or more)")
    print("   - LAST USED should update for the API key")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(make_direct_api_calls())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
