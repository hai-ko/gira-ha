#!/usr/bin/env python3
"""Test script to discover available API endpoints on Gira X1."""

import asyncio
import aiohttp
import json
import sys
from base64 import b64encode

async def test_api_endpoints():
    """Test various API endpoints to find what's available."""
    
    # Configuration from your example_configuration.yaml
    host = "10.1.1.85"
    port = 443
    token = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"
    
    base_url = f"https://{host}:{port}"
    
    # Prepare authorization header
    auth_header = {"Authorization": f"Bearer {token}"}
    
    # List of endpoints to test
    endpoints_to_test = [
        # API without version (test first)
        "/api",
        "/api/uiconfig",
        "/api/values",
        "/api/uiconfig/uid",
        "/api/clients",
        
        # API v2 endpoints (current)
        "/api/v2",
        "/api/v2/clients",
        "/api/v2/uiconfig",
        "/api/v2/uiconfig/uid", 
        "/api/v2/values",
        "/api/v2/licenses",
        
        # API v1 endpoints (fallback)
        "/api/v1",
        "/api/v1/clients",
        "/api/v1/uiconfig",
        "/api/v1/uiconfig/uid",
        "/api/v1/values",
        "/api/v1/licenses",
        
        # Other possible endpoints
        "/api",
        "/api/status",
        "/api/info",
        "/rest/v2/values",
        "/rest/v1/values",
        "/rest/values",
        
        # Common IoT API patterns
        "/api/v2/data",
        "/api/v2/datapoints",
        "/api/v2/devices",
        "/api/v2/functions",
    ]
    
    print(f"Testing API endpoints on Gira X1 at {base_url}")
    print("=" * 60)
    
    # Create HTTP session with SSL verification disabled (common for local devices)
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        
        working_endpoints = []
        
        for endpoint in endpoints_to_test:
            url = f"{base_url}{endpoint}"
            
            try:
                async with session.get(url, headers=auth_header) as response:
                    status = response.status
                    
                    if status == 200:
                        try:
                            content = await response.text()
                            # Try to parse as JSON
                            if content.strip().startswith('{') or content.strip().startswith('['):
                                data = json.loads(content)
                                print(f"✅ {endpoint} - Status: {status} - JSON response ({len(str(data))} chars)")
                                working_endpoints.append((endpoint, status, "JSON"))
                                
                                # Show structure for important endpoints
                                if endpoint in ["/api/v2/uiconfig", "/api/v1/uiconfig"]:
                                    if isinstance(data, dict) and "functions" in data:
                                        print(f"   📋 UI Config: {len(data.get('functions', []))} functions found")
                                elif endpoint in ["/api/v2/values", "/api/v1/values"]:
                                    if isinstance(data, dict):
                                        print(f"   📊 Values: {len(data)} data points")
                                    elif isinstance(data, list):
                                        print(f"   📊 Values: {len(data)} data points")
                            else:
                                print(f"✅ {endpoint} - Status: {status} - Text response ({len(content)} chars)")
                                working_endpoints.append((endpoint, status, "Text"))
                        except json.JSONDecodeError:
                            content = await response.text()
                            print(f"✅ {endpoint} - Status: {status} - Non-JSON response ({len(content)} chars)")
                            working_endpoints.append((endpoint, status, "Non-JSON"))
                    
                    elif status == 401:
                        print(f"🔒 {endpoint} - Status: {status} - Unauthorized (authentication issue)")
                    elif status == 404:
                        print(f"❌ {endpoint} - Status: {status} - Not Found")
                    elif status == 403:
                        print(f"🚫 {endpoint} - Status: {status} - Forbidden")
                    else:
                        print(f"⚠️  {endpoint} - Status: {status} - Other error")
                        
            except aiohttp.ClientError as e:
                print(f"💥 {endpoint} - Connection error: {e}")
            except asyncio.TimeoutError:
                print(f"⏰ {endpoint} - Timeout")
            except Exception as e:
                print(f"💥 {endpoint} - Unexpected error: {e}")
        
        print("\n" + "=" * 60)
        print("SUMMARY OF WORKING ENDPOINTS:")
        print("=" * 60)
        
        if working_endpoints:
            for endpoint, status, content_type in working_endpoints:
                print(f"✅ {endpoint} ({status}) - {content_type}")
                
            # Determine the correct API version
            v2_endpoints = [ep for ep, _, _ in working_endpoints if ep.startswith("/api/v2")]
            v1_endpoints = [ep for ep, _, _ in working_endpoints if ep.startswith("/api/v1")]
            
            if v2_endpoints:
                print(f"\n🎯 RECOMMENDATION: Use API v2")
                print(f"   Available v2 endpoints: {[ep for ep, _, _ in working_endpoints if ep.startswith('/api/v2')]}")
            elif v1_endpoints:
                print(f"\n🎯 RECOMMENDATION: Use API v1 (v2 not available)")
                print(f"   Available v1 endpoints: {[ep for ep, _, _ in working_endpoints if ep.startswith('/api/v1')]}")
            else:
                print(f"\n⚠️  Neither v1 nor v2 standard endpoints work. Check custom endpoints:")
                for endpoint, status, content_type in working_endpoints:
                    if not endpoint.startswith("/api/v"):
                        print(f"   {endpoint}")
        else:
            print("❌ No working endpoints found!")
            print("\nPossible issues:")
            print("- Wrong token/authentication")
            print("- Wrong host/port")
            print("- Device doesn't support REST API")
            print("- SSL/TLS certificate issues")

if __name__ == "__main__":
    print("Testing Gira X1 API endpoints...")
    print("Using configuration from example_configuration.yaml")
    print("Host: 10.1.1.85, Port: 443, Token auth")
    print()
    
    asyncio.run(test_api_endpoints())
