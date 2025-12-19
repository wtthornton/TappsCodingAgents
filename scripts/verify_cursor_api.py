"""
Verify Cursor Background Agents API endpoints.

Tests actual API endpoints to determine what's available.
This script helps verify which Cursor API endpoints exist and work.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests  # type: ignore[import-untyped]

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def verify_api_endpoints() -> dict[str, Any]:
    """
    Test Cursor API endpoints and document findings.

    Returns:
        Dictionary with verification results
    """
    api_key = os.getenv("CURSOR_API_KEY")
    base_url = "https://api.cursor.com/v0"
    
    results: dict[str, Any] = {
        "api_key_provided": api_key is not None,
        "base_url": base_url,
        "endpoints_tested": [],
        "endpoints_working": [],
        "endpoints_failed": [],
        "endpoints_not_found": [],
        "recommendations": [],
    }
    
    if not api_key:
        results["recommendations"].append(
            "Set CURSOR_API_KEY environment variable to test API endpoints"
        )
        return results
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    # Test endpoints based on research and documentation
    endpoints_to_test = [
        {
            "method": "GET",
            "path": "/agents",
            "description": "List available Background Agents",
            "payload": None,
        },
        {
            "method": "POST",
            "path": "/background-agents/create",
            "description": "Create a Background Agent",
            "payload": {
                "name": "test-agent",
                "description": "Test agent for verification",
            },
        },
        {
            "method": "GET",
            "path": "/background-agents/{id}/status",
            "description": "Get Background Agent status",
            "payload": None,
            "note": "Requires agent ID - will test with placeholder",
        },
    ]
    
    for endpoint in endpoints_to_test:
        method = endpoint["method"]
        path = endpoint["path"]
        description = endpoint["description"]
        
        results["endpoints_tested"].append({
            "method": method,
            "path": path,
            "description": description,
        })
        
        url = f"{base_url}{path}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(
                    url, headers=headers, json=endpoint.get("payload"), timeout=10
                )
            else:
                results["endpoints_failed"].append({
                    "method": method,
                    "path": path,
                    "error": f"Unsupported method: {method}",
                })
                continue
            
            status_code = response.status_code
            
            if status_code == 200 or status_code == 201:
                results["endpoints_working"].append({
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "description": description,
                })
            elif status_code == 404:
                results["endpoints_not_found"].append({
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "description": description,
                })
            elif status_code == 401:
                results["endpoints_failed"].append({
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "error": "Unauthorized - check API key",
                })
            else:
                results["endpoints_failed"].append({
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "error": response.text[:200] if response.text else "Unknown error",
                })
        
        except requests.exceptions.RequestException as e:
            results["endpoints_failed"].append({
                "method": method,
                "path": path,
                "error": str(e),
            })
    
    # Generate recommendations
    if results["endpoints_working"]:
        results["recommendations"].append(
            "Some API endpoints are working - implement verified endpoints only"
        )
    elif results["endpoints_not_found"]:
        results["recommendations"].append(
            "API endpoints not found - use file-based coordination as primary method"
        )
    else:
        results["recommendations"].append(
            "Unable to verify API - maintain graceful degradation to file-based"
        )
    
    return results


def main() -> None:
    """Main entry point for verification script."""
    print("Verifying Cursor Background Agents API endpoints...")
    print("=" * 60)
    
    results = verify_api_endpoints()
    
    # Print results
    print(f"\nAPI Key Provided: {results['api_key_provided']}")
    print(f"Base URL: {results['base_url']}")
    print(f"\nEndpoints Tested: {len(results['endpoints_tested'])}")
    print(f"Endpoints Working: {len(results['endpoints_working'])}")
    print(f"Endpoints Not Found: {len(results['endpoints_not_found'])}")
    print(f"Endpoints Failed: {len(results['endpoints_failed'])}")
    
    if results["endpoints_working"]:
        print("\n✅ Working Endpoints:")
        for endpoint in results["endpoints_working"]:
            print(f"  - {endpoint['method']} {endpoint['path']}")
    
    if results["endpoints_not_found"]:
        print("\n❌ Not Found Endpoints:")
        for endpoint in results["endpoints_not_found"]:
            print(f"  - {endpoint['method']} {endpoint['path']}")
    
    if results["endpoints_failed"]:
        print("\n⚠️  Failed Endpoints:")
        for endpoint in results["endpoints_failed"]:
            print(f"  - {endpoint['method']} {endpoint['path']}: {endpoint.get('error', 'Unknown error')}")
    
    if results["recommendations"]:
        print("\n📋 Recommendations:")
        for rec in results["recommendations"]:
            print(f"  - {rec}")
    
    # Save results to file
    output_file = project_root / "docs" / "CURSOR_API_VERIFICATION.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Cursor Background Agents API Verification Results\n\n")
        f.write(f"**Date**: {__import__('datetime').datetime.now().isoformat()}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- API Key Provided: {results['api_key_provided']}\n")
        f.write(f"- Endpoints Tested: {len(results['endpoints_tested'])}\n")
        f.write(f"- Endpoints Working: {len(results['endpoints_working'])}\n")
        f.write(f"- Endpoints Not Found: {len(results['endpoints_not_found'])}\n")
        f.write(f"- Endpoints Failed: {len(results['endpoints_failed'])}\n\n")
        
        if results["endpoints_working"]:
            f.write("## Working Endpoints\n\n")
            for endpoint in results["endpoints_working"]:
                f.write(f"- `{endpoint['method']} {endpoint['path']}`\n")
            f.write("\n")
        
        if results["endpoints_not_found"]:
            f.write("## Not Found Endpoints\n\n")
            for endpoint in results["endpoints_not_found"]:
                f.write(f"- `{endpoint['method']} {endpoint['path']}`\n")
            f.write("\n")
        
        if results["endpoints_failed"]:
            f.write("## Failed Endpoints\n\n")
            for endpoint in results["endpoints_failed"]:
                f.write(f"- `{endpoint['method']} {endpoint['path']}`: {endpoint.get('error', 'Unknown error')}\n")
            f.write("\n")
        
        if results["recommendations"]:
            f.write("## Recommendations\n\n")
            for rec in results["recommendations"]:
                f.write(f"- {rec}\n")
            f.write("\n")
        
        f.write("## Full Results (JSON)\n\n")
        f.write("```json\n")
        f.write(json.dumps(results, indent=2))
        f.write("\n```\n")
    
    print(f"\n📄 Results saved to: {output_file}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

