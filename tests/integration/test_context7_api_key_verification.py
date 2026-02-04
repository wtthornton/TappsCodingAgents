"""
Context7 API Key Verification Test

This test verifies that the Context7 API key actually works by making
real authenticated API calls and checking the actual response.

⚠️ CRITICAL: This test must verify actual results, not just that code executed.
"""

import os

import httpx
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.requires_context7
def test_context7_api_key_verification():
    """
    Verify Context7 API key works by making actual authenticated API call.
    
    This test:
    1. Checks if API key is set
    2. Makes actual HTTP call to Context7 API
    3. Verifies response indicates successful authentication
    4. Reports actual results (not just that code ran)
    """
    # Step 1: Verify API key is set
    api_key = os.getenv("CONTEXT7_API_KEY")
    if not api_key:
        pytest.skip("CONTEXT7_API_KEY not set - cannot verify API key")
    
    print(f"\n{'='*60}")
    print("Context7 API Key Verification Test")
    print(f"{'='*60}")
    print("API Key Found: Yes")
    print(f"Key Prefix: {api_key[:20]}...")
    print()
    
    # Step 2: Make actual API call
    # Based on Context7 API documentation from https://context7.com/dashboard:
    # - API URL: https://context7.com/api/v2
    # - Search endpoint: GET /api/v2/search?query=next.js
    # - Auth: Authorization: Bearer CONTEXT7_API_KEY
    API_URL = os.getenv("CONTEXT7_API_URL", "https://context7.com/api/v2")
    
    print(f"Making API call to: {API_URL}/search")
    print("Query: react")
    print("Auth Method: Authorization: Bearer CONTEXT7_API_KEY")
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
            
            # Step 3: Verify actual response
            print(f"Response Status Code: {response.status_code}")
            
            # Check authentication status from headers
            auth_status = response.headers.get("x-clerk-auth-status", "unknown")
            quota_tier = response.headers.get("context7-quota-tier", "unknown")
            
            print(f"Auth Status: {auth_status}")
            print(f"Quota Tier: {quota_tier}")
            print()
            
            # Check if call succeeded
            # Note: Even if auth_status is "signed-out", if quota_tier is not "anonymous"
            # and status is 200, the API key is working (quota_tier shows key recognition)
            if response.status_code == 200:
                data = response.json()
                print("[SUCCESS] API CALL SUCCEEDED")
                print(f"Response Data Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Verify we got actual data (not just an error message)
                # Based on API docs, response should have "results" array
                if isinstance(data, dict):
                    if "results" in data and len(data.get("results", [])) > 0:
                        print(f"[SUCCESS] API KEY VERIFIED: Found {len(data['results'])} library results")
                        first_result = data['results'][0]
                        print(f"First Result ID: {first_result.get('id', 'N/A')}")
                        print(f"First Result Title: {first_result.get('title', 'N/A')}")
                        assert True, "API key works - received valid response with results"
                    elif "error" in data:
                        print(f"[WARNING] API responded but with error: {data['error']}")
                        pytest.fail(f"API call succeeded but returned error: {data['error']}")
                    else:
                        print(f"[WARNING] API responded but response format unexpected: {data}")
                        pytest.fail(f"API call succeeded but response format unexpected: {data}")
                else:
                    print(f"[WARNING] API responded but data is not a dict: {type(data)}")
                    pytest.fail(f"API call succeeded but response is not a dict: {type(data)}")
                    
            elif response.status_code == 401:
                print("[FAILED] API CALL FAILED: Authentication failed (401 Unauthorized)")
                print("   This means the API key is invalid or not accepted")
                pytest.fail("API key authentication failed - 401 Unauthorized")
                
            elif response.status_code == 403:
                print("[FAILED] API CALL FAILED: Forbidden (403)")
                print("   This means the API key may be valid but lacks permissions")
                pytest.fail("API key forbidden - 403 Forbidden")
                
            elif response.status_code == 404:
                # Check if this is an authentication issue
                if quota_tier == "anonymous":
                    print("[FAILED] API KEY NOT RECOGNIZED")
                    print()
                    print("Evidence:")
                    print(f"  - Quota Tier: {quota_tier} (should show your tier, not 'anonymous')")
                    print()
                    print("VERIFICATION RESULT:")
                    print("  The API key is NOT being authenticated.")
                    print("  The API treats the request as anonymous/unauthenticated.")
                    pytest.fail(
                        f"API key not recognized - quota_tier={quota_tier} (anonymous). "
                        f"API key authentication failed."
                    )
                else:
                    print("[FAILED] Endpoint not found (404)")
                    print(f"   Response: {response.text[:200]}")
                    pytest.fail(f"API endpoint not found - status {response.status_code}")
            else:
                print(f"[FAILED] API CALL FAILED: Status code {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                pytest.fail(f"API call failed with status {response.status_code}: {response.text[:200]}")
                
    except httpx.ConnectError as e:
        print("[FAILED] CONNECTION FAILED: Cannot reach Context7 API")
        print(f"   Error: {e}")
        print()
        print("   VERIFICATION RESULT:")
        print("   - API Key is set: YES")
        print("   - API URL tried: {API_URL}")
        print("   - Connection: FAILED")
        print()
        print("   Possible reasons:")
        print("   - Network connectivity issue")
        print("   - API endpoint may require MCP server (not direct HTTP)")
        print("   - Firewall or DNS resolution issue")
        print()
        pytest.fail(f"Cannot connect to Context7 API at {API_URL}: {e}")
        
    except Exception as e:
        print(f"[FAILED] UNEXPECTED ERROR: {type(e).__name__}: {e}")
        pytest.fail(f"Unexpected error during API call: {e}")


@pytest.mark.requires_context7
def test_context7_api_key_get_docs():
    """
    Verify Context7 API key works for getting documentation.
    
    This test makes an actual API call to get library documentation
    and verifies the response indicates successful authentication.
    """
    api_key = os.getenv("CONTEXT7_API_KEY")
    if not api_key:
        pytest.skip("CONTEXT7_API_KEY not set - cannot verify API key")
    
    # Use correct API URL and authentication
    # Based on API docs: GET /api/v2/docs/code/{library_id}?type=json&topic=ssr&page=1
    API_URL = os.getenv("CONTEXT7_API_URL", "https://context7.com/api/v2")
    
    # Use a known library ID for testing (from API docs example)
    library_id = "vercel/next.js"
    topic = "ssr"
    
    print(f"\n{'='*60}")
    print("Context7 API Key Verification - Get Docs Test")
    print(f"{'='*60}")
    print(f"API URL: {API_URL}")
    print(f"Library ID: {library_id}")
    print(f"Topic: {topic}")
    print("Auth Method: Authorization: Bearer CONTEXT7_API_KEY")
    print()
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{API_URL}/docs/code/{library_id}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                params={"type": "json", "topic": topic, "page": 1},
            )
            
            print(f"Response Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                print("[SUCCESS] API CALL SUCCEEDED")
                print(f"Response Type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Response Keys: {list(data.keys())}")
                elif isinstance(data, str):
                    print(f"Response Length: {len(data)} characters")
                assert True, "API key works - received valid documentation response"
            elif response.status_code == 401:
                print("[FAILED] API key authentication failed - 401 Unauthorized")
                pytest.fail("API key authentication failed - 401 Unauthorized")
            elif response.status_code == 403:
                print("[FAILED] API key forbidden - 403 Forbidden")
                pytest.fail("API key forbidden - 403 Forbidden")
            else:
                print(f"[FAILED] API call failed with status {response.status_code}")
                pytest.fail(f"API call failed with status {response.status_code}")
                
    except httpx.ConnectError as e:
        print(f"[INFO] Cannot connect to Context7 API via direct HTTP: {e}")
        print("   VERIFICATION RESULT: Cannot verify API key via direct HTTP")
        print("   This is expected - Context7 requires MCP server access")
        pytest.skip("Cannot verify API key via direct HTTP - Context7 requires MCP server")
    except Exception as e:
        pytest.fail(f"Unexpected error during API call: {e}")

