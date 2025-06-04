#!/usr/bin/env python3
"""
Test callback endpoints through HTTPS proxy.

This test verifies that the callback endpoints are reachable through the new
HTTPS proxy at https://home.hf17-1.de, which should resolve the SSL/TLS issues
we found with the direct IP connection.
"""

import asyncio
import aiohttp
import json
import sys

# Configuration with new HTTPS proxy
HTTPS_PROXY_URL = "https://home.hf17-1.de"
HOME_ASSISTANT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmOGYwZjM4NDk4ZjE0ZmZjODMwZmI0MTdlMWU1ZWRhYiIsImlhdCI6MTczMzI0ODQ3NSwiZXhwIjoyMDQ4NjA4NDc1fQ.3q2rZfBBwk9yP_WjlFN_2xHF7trnHbnJTLyEpFMN4Ao"

# Callback URLs through proxy
VALUE_CALLBACK_URL = f"{HTTPS_PROXY_URL}/api/gira_x1/callback/value"
SERVICE_CALLBACK_URL = f"{HTTPS_PROXY_URL}/api/gira_x1/callback/service"


async def test_basic_https_connectivity():
    """Test basic HTTPS connectivity to the proxy."""
    print("🌐 Testing basic HTTPS connectivity through proxy...")
    print(f"   Target: {HTTPS_PROXY_URL}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test basic Home Assistant API through proxy
            api_url = f"{HTTPS_PROXY_URL}/api/"
            headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
            
            async with session.get(api_url, headers=headers) as response:
                print(f"   ✅ HTTPS proxy connectivity SUCCESS: HTTP {response.status}")
                return True
                
    except aiohttp.ClientConnectorError as e:
        print(f"   ❌ HTTPS proxy connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ HTTPS proxy error: {e}")
        return False


async def test_callback_endpoint_through_proxy(url: str, callback_type: str) -> bool:
    """Test a callback endpoint through the HTTPS proxy."""
    print(f"\n🔔 Testing {callback_type} callback through proxy:")
    print(f"   URL: {url}")
    
    # Test payload (simulating what Gira X1 sends)
    if callback_type == "value":
        payload = {
            "uid": "test_proxy_callback",
            "value": 42,
            "timestamp": "2025-06-04T10:30:00.000Z"
        }
    else:  # service
        payload = {
            "service": "proxy_test",
            "event": "validation",
            "timestamp": "2025-06-04T10:30:00.000Z"
        }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Gira-X1-Proxy-Test",
        "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)  # Slightly longer for proxy
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print(f"   📤 Sending: {json.dumps(payload, indent=6)}")
            
            async with session.post(url, json=payload, headers=headers) as response:
                status = response.status
                print(f"   📥 Response status: {status}")
                
                try:
                    response_text = await response.text()
                    print(f"   📥 Response body: {response_text}")
                except:
                    print(f"   📥 Response body: <could not read>")
                
                if 200 <= status < 300:
                    print(f"   ✅ {callback_type} callback through proxy SUCCESS")
                    return True
                else:
                    print(f"   ❌ {callback_type} callback through proxy FAILED (HTTP {status})")
                    return False
                    
    except aiohttp.ClientConnectorError as e:
        print(f"   ❌ Proxy connection error: {e}")
        return False
    except asyncio.TimeoutError:
        print(f"   ❌ Timeout through proxy")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected proxy error: {e}")
        return False


async def test_webhook_endpoints_exist():
    """Test if webhook endpoints are properly registered through proxy."""
    print(f"\n📋 Testing webhook endpoint registration through proxy...")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test value callback endpoint (GET should return 405)
            async with session.get(VALUE_CALLBACK_URL, headers=headers) as response:
                print(f"   Value callback GET: HTTP {response.status}")
                value_exists = response.status == 405  # Method Not Allowed means endpoint exists
                
            # Test service callback endpoint (GET should return 405)
            async with session.get(SERVICE_CALLBACK_URL, headers=headers) as response:
                print(f"   Service callback GET: HTTP {response.status}")
                service_exists = response.status == 405  # Method Not Allowed means endpoint exists
            
            if value_exists and service_exists:
                print("   ✅ Both callback endpoints are registered and accessible through proxy")
                return True
            elif response.status == 404:
                print("   ❌ Callback endpoints not found (404) - integration may not be loaded")
                return False
            else:
                print(f"   ⚠️ Unexpected endpoint status - check integration")
                return False
                
    except Exception as e:
        print(f"   ❌ Webhook endpoint test error: {e}")
        return False


async def main():
    """Test callback endpoints through HTTPS proxy."""
    print("🔗 HTTPS PROXY CALLBACK TEST")
    print("=" * 40)
    print(f"HTTPS Proxy: {HTTPS_PROXY_URL}")
    print(f"Token: {HOME_ASSISTANT_TOKEN[:20]}...")
    
    # Test 1: Basic proxy connectivity
    basic_ok = await test_basic_https_connectivity()
    
    if not basic_ok:
        print(f"\n❌ CRITICAL: Cannot connect to HTTPS proxy")
        print(f"   Check proxy configuration and network connectivity")
        return False
    
    # Test 2: Webhook endpoint registration
    endpoints_ok = await test_webhook_endpoints_exist()
    
    if not endpoints_ok:
        print(f"\n❌ CRITICAL: Callback endpoints not accessible through proxy")
        print(f"   Check that Gira X1 integration is loaded in Home Assistant")
        return False
    
    # Test 3: Test actual callback functionality
    value_success = await test_callback_endpoint_through_proxy(VALUE_CALLBACK_URL, "value")
    service_success = await test_callback_endpoint_through_proxy(SERVICE_CALLBACK_URL, "service")
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"HTTPS Proxy:          {'✅ PASS' if basic_ok else '❌ FAIL'}")
    print(f"Endpoint Registration: {'✅ PASS' if endpoints_ok else '❌ FAIL'}")
    print(f"Value Callback:       {'✅ PASS' if value_success else '❌ FAIL'}")
    print(f"Service Callback:     {'✅ PASS' if service_success else '❌ FAIL'}")
    
    if basic_ok and endpoints_ok and value_success and service_success:
        print(f"\n🎉 SUCCESS!")
        print(f"   All callback endpoints work through HTTPS proxy")
        print(f"   Gira X1 should be able to register callbacks successfully")
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Update Gira X1 integration to use proxy URLs")
        print(f"   2. Test callback registration with Gira X1")
        print(f"   3. Verify real-time updates are working")
    else:
        print(f"\n❌ ISSUES FOUND:")
        if not basic_ok:
            print(f"   - HTTPS proxy not accessible")
        if not endpoints_ok:
            print(f"   - Callback endpoints not properly registered")
        if not value_success or not service_success:
            print(f"   - Callback processing not working through proxy")
    
    return basic_ok and endpoints_ok and value_success and service_success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        sys.exit(1)
