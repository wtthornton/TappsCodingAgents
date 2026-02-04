"""
Test correct Context7 API endpoints:
- Search: /api/v2/libs/search?libraryName=...&query=...
- Context: /api/v2/context?libraryId=...&query=...&type=...
"""

import asyncio
import os
import sys

if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except:
        pass

import httpx

API_KEY = "ctx7sk-6aaa23b8-28f9-4d89-a83f-598ea16eb1c0"
BASE_URL = "https://context7.com/api/v2"


async def test():
    print("=" * 60)
    print("Testing CORRECT Context7 API endpoints")
    print("=" * 60)
    print(f"API Key: {API_KEY[:12]}...{API_KEY[-4:]}")
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Call 1: Search endpoint (correct path)
        print("\n" + "-" * 40)
        print("Call 1: GET /api/v2/libs/search")
        print("  Params: libraryName=fastapi, query=routing")
        print("-" * 40)
        
        url = f"{BASE_URL}/libs/search"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        params = {"libraryName": "fastapi", "query": "routing"}
        
        resp = await client.get(url, headers=headers, params=params)
        print(f"Status Code: {resp.status_code}")
        print(f"Headers: ratelimit-remaining={resp.headers.get('ratelimit-remaining', 'N/A')}")
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            print(f"SUCCESS! Found {len(results)} results")
            if results:
                first = results[0]
                print("  First match:")
                print(f"    ID: {first.get('id', 'N/A')}")
                print(f"    Title: {first.get('title', 'N/A')}")
        elif resp.status_code == 429:
            print(f"QUOTA EXCEEDED: {resp.text[:200]}")
        else:
            print(f"ERROR: {resp.text[:300]}")
        
        # Call 2: Context endpoint
        print("\n" + "-" * 40)
        print("Call 2: GET /api/v2/context")
        print("  Params: libraryId=/tiangolo/fastapi, query=routing, type=json")
        print("-" * 40)
        
        url2 = f"{BASE_URL}/context"
        params2 = {"libraryId": "/tiangolo/fastapi", "query": "routing", "type": "json"}
        
        resp2 = await client.get(url2, headers=headers, params=params2)
        print(f"Status Code: {resp2.status_code}")
        print(f"Headers: ratelimit-remaining={resp2.headers.get('ratelimit-remaining', 'N/A')}")
        
        if resp2.status_code == 200:
            print("SUCCESS! Got documentation")
            print(f"Response preview: {resp2.text[:300]}...")
        elif resp2.status_code == 429:
            print(f"QUOTA EXCEEDED: {resp2.text[:200]}")
        else:
            print(f"ERROR: {resp2.text[:300]}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("Check your Context7 dashboard:")
    print("  - REQUESTS should increase")
    print("  - TappsCodingAgents key LAST USED should update")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test())
