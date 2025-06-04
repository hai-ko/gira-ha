#!/usr/bin/env python3
"""
Test callback endpoint connectivity from Gira X1's perspective.

This script simulates what the Gira X1 does when trying to reach Home Assistant callback endpoints.
It tests both value and service callback URLs with proper authentication and payload formats.
"""

import asyncio
import aiohttp
import json
import ssl
import sys
from typing import Dict, Any
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration - Update these to match your setup
GIRA_X1_IP = "10.1.1.85"
HOME_ASSISTANT_IP = "10.1.1.242"
HOME_ASSISTANT_PORT = 8123
HOME_ASSISTANT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmOGYwZjM4NDk4ZjE0ZmZjODMwZmI0MTdlMWU1ZWRhYiIsImlhdCI6MTczMzI0ODQ3NSwiZXhwIjoyMDQ4NjA4NDc1fQ.3q2rZfBBwk9yP_WjlFN_2xHF7trnHbnJTLyEpFMN4Ao"

# Callback URLs (what Gira X1 tries to reach)
VALUE_CALLBACK_URL = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/value"
SERVICE_CALLBACK_URL = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/service"

# Test payloads (simulating what Gira X1 sends)
VALUE_CALLBACK_PAYLOAD = {
    "uid": "test_datapoint_123",
    "value": 42,
    "timestamp": "2025-06-04T10:30:00.000Z"
}

SERVICE_CALLBACK_PAYLOAD = {
    "service": "test_service",
    "event": "test_event",
    "timestamp": "2025-06-04T10:30:00.000Z",
    "data": {"test": "value"}
}


async def test_callback_endpoint(
    session: aiohttp.ClientSession,
    url: str,
    payload: Dict[str, Any],
    callback_type: str
) -> bool:
    """Test a specific callback endpoint."""
    print(f"\n🔗 Testing {callback_type} callback endpoint:")
    print(f"   URL: {url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Gira-X1-Callback-Test",
        "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"
    }
    
    try:
        # Test with timeout (Gira X1 has limited patience)
        async with session.post(
            url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=10),
            ssl=False  # Disable SSL verification for self-signed certs
        ) as response:
            print(f"✅ Connection successful!")
            print(f"   Status: {response.status}")
            print(f"   Headers: {dict(response.headers)}")
            
            try:
                response_text = await response.text()
                print(f"   Response: {response_text}")
            except Exception as e:
                print(f"   Could not read response body: {e}")
            
            # Consider 2xx status codes as success
            if 200 <= response.status < 300:
                print(f"✅ {callback_type} callback endpoint is reachable and responding correctly")
                return True
            else:
                print(f"⚠️ {callback_type} callback endpoint reachable but returned error status {response.status}")
                return False
                
    except aiohttp.ClientConnectorError as e:
        print(f"❌ Connection failed: {e}")
        print(f"   This means Gira X1 cannot establish a network connection to Home Assistant")
        return False
    except asyncio.TimeoutError:
        print(f"❌ Request timeout")
        print(f"   Home Assistant didn't respond within 10 seconds")
        return False
    except aiohttp.ClientSSLError as e:
        print(f"❌ SSL/TLS error: {e}")
        print(f"   This could indicate HTTPS configuration issues")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


async def test_basic_connectivity() -> bool:
    """Test basic HTTP connectivity to Home Assistant."""
    print(f"\n🌐 Testing basic connectivity to Home Assistant...")
    print(f"   Target: https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}")
    
    # Create SSL context that ignores certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            # Test basic API endpoint
            test_url = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/"
            headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
            
            async with session.get(
                test_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f"✅ Basic HTTP connectivity works!")
                print(f"   Status: {response.status}")
                return True
                
    except Exception as e:
        print(f"❌ Basic connectivity failed: {e}")
        return False


async def test_webhook_registration() -> bool:
    """Test if webhook endpoints are properly registered in Home Assistant."""
    print(f"\n📋 Testing webhook endpoint registration...")
    
    # Create SSL context that ignores certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            # Test if endpoints exist (should return method not allowed for GET)
            headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
            
            # Test value callback endpoint
            async with session.get(
                VALUE_CALLBACK_URL,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                print(f"Value callback endpoint status: {response.status}")
                # 405 (Method Not Allowed) means endpoint exists but doesn't accept GET
                # 404 means endpoint doesn't exist
                if response.status == 405:
                    print("✅ Value callback endpoint is registered (returns 405 for GET)")
                elif response.status == 404:
                    print("❌ Value callback endpoint not found (404)")
                    return False
                else:
                    print(f"⚠️ Unexpected status for value callback: {response.status}")
            
            # Test service callback endpoint
            async with session.get(
                SERVICE_CALLBACK_URL,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                print(f"Service callback endpoint status: {response.status}")
                if response.status == 405:
                    print("✅ Service callback endpoint is registered (returns 405 for GET)")
                elif response.status == 404:
                    print("❌ Service callback endpoint not found (404)")
                    return False
                else:
                    print(f"⚠️ Unexpected status for service callback: {response.status}")
            
            return True
            
    except Exception as e:
        print(f"❌ Webhook registration test failed: {e}")
        return False


async def simulate_gira_x1_callback_test() -> bool:
    """Simulate the exact callback test that Gira X1 performs during registration."""
    print(f"\n🧪 Simulating Gira X1's callback test...")
    
    # Create SSL context that ignores certificate verification (like Gira X1)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    success_count = 0
    total_tests = 2
    
    try:
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30)  # Gira X1 might be patient
        ) as session:
            
            # Test value callback
            value_success = await test_callback_endpoint(
                session, VALUE_CALLBACK_URL, VALUE_CALLBACK_PAYLOAD, "value"
            )
            if value_success:
                success_count += 1
            
            # Test service callback
            service_success = await test_callback_endpoint(
                session, SERVICE_CALLBACK_URL, SERVICE_CALLBACK_PAYLOAD, "service"
            )
            if service_success:
                success_count += 1
            
    except Exception as e:
        print(f"❌ Callback simulation failed: {e}")
        return False
    
    print(f"\n📊 Callback Test Summary:")
    print(f"   Successful callbacks: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✅ All callback tests passed - Gira X1 should be able to register callbacks")
        return True
    else:
        print("❌ Some callback tests failed - This explains why Gira X1 callback registration fails")
        return False


async def check_network_route() -> None:
    """Check network routing from this machine to Home Assistant."""
    print(f"\n🛣️ Network routing analysis:")
    print(f"   Testing from current machine to {HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}")
    print(f"   (This simulates the network path Gira X1 would use)")
    
    import socket
    
    try:
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((HOME_ASSISTANT_IP, HOME_ASSISTANT_PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ TCP connection to {HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT} successful")
        else:
            print(f"❌ TCP connection failed with error code: {result}")
            
    except Exception as e:
        print(f"❌ TCP connection test failed: {e}")


def print_diagnostics():
    """Print diagnostic information."""
    print("🔍 CALLBACK ENDPOINT CONNECTIVITY TEST")
    print("=" * 50)
    print(f"Gira X1 IP: {GIRA_X1_IP}")
    print(f"Home Assistant IP: {HOME_ASSISTANT_IP}")
    print(f"Home Assistant Port: {HOME_ASSISTANT_PORT}")
    print(f"Value Callback URL: {VALUE_CALLBACK_URL}")
    print(f"Service Callback URL: {SERVICE_CALLBACK_URL}")
    print(f"Using HA Token: {HOME_ASSISTANT_TOKEN[:20]}...")


async def main():
    """Run all connectivity tests."""
    print_diagnostics()
    
    # Test 1: Basic connectivity
    basic_ok = await test_basic_connectivity()
    
    # Test 2: Network routing
    await check_network_route()
    
    # Test 3: Webhook registration
    webhook_ok = await test_webhook_registration()
    
    # Test 4: Simulate actual callback tests
    callback_ok = await simulate_gira_x1_callback_test()
    
    # Summary
    print(f"\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS:")
    print("=" * 50)
    print(f"✅ Basic connectivity: {'PASS' if basic_ok else 'FAIL'}")
    print(f"✅ Webhook endpoints: {'PASS' if webhook_ok else 'FAIL'}")
    print(f"✅ Callback simulation: {'PASS' if callback_ok else 'FAIL'}")
    
    if basic_ok and webhook_ok and callback_ok:
        print(f"\n🎉 SUCCESS: All tests passed!")
        print(f"   Gira X1 should be able to register and use callbacks successfully.")
        print(f"   If callback registration still fails, the issue may be:")
        print(f"   - Gira X1 network configuration")
        print(f"   - Firewall rules on Gira X1 side")
        print(f"   - Different network path from Gira X1 to Home Assistant")
    else:
        print(f"\n❌ ISSUES FOUND:")
        if not basic_ok:
            print(f"   - Basic HTTP connectivity to Home Assistant failed")
            print(f"   - Check Home Assistant is running and accessible")
            print(f"   - Verify IP address and port configuration")
        if not webhook_ok:
            print(f"   - Callback webhook endpoints not properly registered")
            print(f"   - Check that Gira X1 integration is loaded in Home Assistant")
            print(f"   - Verify webhook registration in integration startup")
        if not callback_ok:
            print(f"   - Callback endpoints not responding correctly")
            print(f"   - This explains why Gira X1 callback registration fails")
    
    return basic_ok and webhook_ok and callback_ok


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with unexpected error: {e}")
        sys.exit(1)
