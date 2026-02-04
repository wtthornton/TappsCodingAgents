"""Test different Context7 API authentication methods."""

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
BASE_URL = "https://context7.com/api/v2/libs/search"
PARAMS = {"libraryName": "fastapi", "query": "routing"}


def test_auth():
    print("=" * 60)
    print("Testing Context7 API Authentication Methods")
    print("=" * 60)
    print(f"API Key: {API_KEY[:15]}...{API_KEY[-4:]}")
    print(f"Endpoint: {BASE_URL}")
    print()

    # Method 1: Bearer token (standard OAuth)
    print("-" * 40)
    print("Method 1: Authorization: Bearer {key}")
    print("-" * 40)
    try:
        resp1 = httpx.get(
            BASE_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            params=PARAMS,
            timeout=10
        )
        print(f"Status: {resp1.status_code}")
        print(f"Auth status: {resp1.headers.get('x-clerk-auth-status', 'N/A')}")
        print(f"Auth message: {resp1.headers.get('x-clerk-auth-message', 'N/A')[:80]}")
        if resp1.status_code == 200:
            print("SUCCESS!")
            data = resp1.json()
            print(f"Results: {len(data.get('results', []))} libraries found")
    except Exception as e:
        print(f"Error: {e}")

    # Method 2: X-API-Key header
    print()
    print("-" * 40)
    print("Method 2: X-API-Key: {key}")
    print("-" * 40)
    try:
        resp2 = httpx.get(
            BASE_URL,
            headers={"X-API-Key": API_KEY},
            params=PARAMS,
            timeout=10
        )
        print(f"Status: {resp2.status_code}")
        print(f"Auth status: {resp2.headers.get('x-clerk-auth-status', 'N/A')}")
        if resp2.status_code == 200:
            print("SUCCESS!")
            data = resp2.json()
            print(f"Results: {len(data.get('results', []))} libraries found")
    except Exception as e:
        print(f"Error: {e}")

    # Method 3: api_key query param
    print()
    print("-" * 40)
    print("Method 3: ?api_key={key} (query param)")
    print("-" * 40)
    try:
        params_with_key = {**PARAMS, "api_key": API_KEY}
        resp3 = httpx.get(BASE_URL, params=params_with_key, timeout=10)
        print(f"Status: {resp3.status_code}")
        print(f"Auth status: {resp3.headers.get('x-clerk-auth-status', 'N/A')}")
        if resp3.status_code == 200:
            print("SUCCESS!")
            data = resp3.json()
            print(f"Results: {len(data.get('results', []))} libraries found")
    except Exception as e:
        print(f"Error: {e}")

    # Method 4: apiKey query param
    print()
    print("-" * 40)
    print("Method 4: ?apiKey={key} (camelCase query param)")
    print("-" * 40)
    try:
        params_with_key = {**PARAMS, "apiKey": API_KEY}
        resp4 = httpx.get(BASE_URL, params=params_with_key, timeout=10)
        print(f"Status: {resp4.status_code}")
        print(f"Auth status: {resp4.headers.get('x-clerk-auth-status', 'N/A')}")
        if resp4.status_code == 200:
            print("SUCCESS!")
            data = resp4.json()
            print(f"Results: {len(data.get('results', []))} libraries found")
    except Exception as e:
        print(f"Error: {e}")

    # Method 5: X-Context7-API-Key header
    print()
    print("-" * 40)
    print("Method 5: X-Context7-API-Key: {key}")
    print("-" * 40)
    try:
        resp5 = httpx.get(
            BASE_URL,
            headers={"X-Context7-API-Key": API_KEY},
            params=PARAMS,
            timeout=10
        )
        print(f"Status: {resp5.status_code}")
        print(f"Auth status: {resp5.headers.get('x-clerk-auth-status', 'N/A')}")
        if resp5.status_code == 200:
            print("SUCCESS!")
            data = resp5.json()
            print(f"Results: {len(data.get('results', []))} libraries found")
    except Exception as e:
        print(f"Error: {e}")

    print()
    print("=" * 60)
    print("Test complete")
    print("=" * 60)


if __name__ == "__main__":
    test_auth()
