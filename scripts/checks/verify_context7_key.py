#!/usr/bin/env python3
"""
Direct Context7 API Key Verification Script

This script makes actual API calls to verify the Context7 API key works.
Based on Context7 documentation:
- API URL: https://context7.com/api/v2
- Auth: CONTEXT7_API_KEY header
"""

import os
import sys

import httpx


def main():
    print("=" * 70)
    print("Context7 API Key Verification")
    print("=" * 70)
    print()
    
    # Check API key
    api_key = os.getenv("CONTEXT7_API_KEY")
    if not api_key:
        print("[ERROR] CONTEXT7_API_KEY not set")
        print("Set it with: $env:CONTEXT7_API_KEY='your-key'")
        return 1
    
    print("[OK] API Key Found")
    print(f"     Prefix: {api_key[:20]}...")
    print()
    
    # Based on Context7 API documentation from https://context7.com/dashboard:
    # - API URL: https://context7.com/api/v2
    # - Search endpoint: GET /api/v2/search?query=next.js
    # - Auth: Authorization: Bearer CONTEXT7_API_KEY
    
    API_URL = "https://context7.com/api/v2"
    print("Testing Context7 API:")
    print(f"  URL: {API_URL}/search")
    print("  Query: react")
    print("  Auth: Authorization: Bearer CONTEXT7_API_KEY")
    print()
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{API_URL}/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                params={"query": "react"},
            )
            
            print(f"  Status: {response.status_code}")
            print(f"  Headers: {dict(response.headers)}")
            
            # Check authentication status from headers
            auth_status = response.headers.get("x-clerk-auth-status", "unknown")
            quota_tier = response.headers.get("context7-quota-tier", "unknown")
            
            print(f"  Auth Status: {auth_status}")
            print(f"  Quota Tier: {quota_tier}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                print("[SUCCESS] API KEY WORKS!")
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                if isinstance(data, dict) and "results" in data:
                    results = data.get("results", [])
                    print(f"Found {len(results)} library results")
                    if len(results) > 0:
                        first = results[0]
                        print(f"First result: {first.get('id', 'N/A')} - {first.get('title', 'N/A')}")
                return 0
            elif response.status_code == 401:
                print("[FAILED] Authentication failed (401)")
                print("The API key is invalid or not accepted")
                print(f"Response: {response.text[:200]}")
                return 1
            elif response.status_code == 403:
                print("[FAILED] Forbidden (403)")
                print("The API key may be valid but lacks permissions")
                print(f"Response: {response.text[:200]}")
                return 1
            elif response.status_code == 404:
                print("[RESULT] Endpoint returned 404")
                print(f"Response: {response.text[:200]}")
                print()
                print("VERIFICATION RESULT:")
                print("=" * 70)
                if auth_status == "signed-out" and quota_tier == "anonymous":
                    print("[FAILED] API KEY NOT RECOGNIZED")
                    print()
                    print("Evidence:")
                    print(f"  - Auth Status: {auth_status} (should be 'signed-in')")
                    print(f"  - Quota Tier: {quota_tier} (should show your tier, not 'anonymous')")
                    print()
                    print("This means:")
                    print("  - The API key is NOT being authenticated")
                    print("  - The API treats the request as anonymous/unauthenticated")
                    print("  - The API key format or authentication method may be incorrect")
                    print()
                    print("Possible reasons:")
                    print("  1. API key format is wrong")
                    print("  2. Authentication method is wrong (should use MCP server)")
                    print("  3. Context7 API requires MCP server, not direct HTTP")
                    print()
                    print("CONCLUSION: API key cannot be verified via direct HTTP.")
                    print("The key may be valid for MCP server use, but direct API")
                    print("calls are not working with this authentication method.")
                else:
                    print("  - Endpoint path may be incorrect")
                    print("  - Context7 may require MCP server access")
                print("=" * 70)
                return 1
            else:
                print(f"[FAILED] Unexpected status code: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return 1
                
    except httpx.ConnectError as e:
        print("[FAILED] Cannot connect to Context7 API")
        print(f"Error: {e}")
        print()
        print("This could mean:")
        print("  - Network connectivity issue")
        print("  - API endpoint requires MCP server (not direct HTTP)")
        print("  - DNS resolution failed")
        return 1
    except Exception as e:
        print(f"[FAILED] Unexpected error: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

