#!/usr/bin/env python3
"""
Simple callback endpoint test - simulates Gira X1 trying to reach Home Assistant callbacks.

This test specifically focuses on the callback test that Gira X1 performs during registration.
When Gira X1 registers callbacks with testCallbacks=true, it sends test requests to verify
the endpoints are reachable before completing registration.
"""

import asyncio
import aiohttp
import json
import ssl
import sys

# Configuration
HOME_ASSISTANT_IP = "10.1.1.242"
HOME_ASSISTANT_PORT = 8123
HOME_ASSISTANT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmOGYwZjM4NDk4ZjE0ZmZjODMwZmI0MTdlMWU1ZWRhYiIsImlhdCI6MTczMzI0ODQ3NSwiZXhwIjoyMDQ4NjA4NDc1fQ.3q2rZfBBwk9yP_WjlFN_2xHF7trnHbnJTLyEpFMN4Ao"

# Callback URLs
VALUE_CALLBACK_URL = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/value"
SERVICE_CALLBACK_URL = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/service"


async def test_single_callback(url: str, callback_type: str) -> bool:
    """Test a single callback endpoint."""
    print(f"\n🔔 Testing {callback_type} callback: {url}")
    
    # Test payload (what Gira X1 would send)
    if callback_type == "value":
        payload = {
            "uid": "test_callback_validation",
            "value": 1,
            "timestamp": "2025-06-04T10:30:00.000Z"
        }
    else:  # service
        payload = {
            "service": "callback_test",
            "event": "validation",
            "timestamp": "2025-06-04T10:30:00.000Z"
        }
    
    # Headers (simulating Gira X1)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Gira-X1-Callback-Validator",
        "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"
    }
    
    # SSL context (Gira X1 accepts self-signed certs)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=10)  # Gira X1 timeout
    
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
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
                    print(f"   ✅ {callback_type} callback SUCCESS")
                    return True
                else:
                    print(f"   ❌ {callback_type} callback FAILED (HTTP {status})")
                    return False
                    
    except aiohttp.ClientConnectorError as e:
        print(f"   ❌ Connection error: {e}")
        print(f"   💡 This means Gira X1 cannot reach Home Assistant")
        return False
    except asyncio.TimeoutError:
        print(f"   ❌ Timeout after 10 seconds")
        print(f"   💡 Home Assistant didn't respond fast enough")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


async def main():
    """Run the callback endpoint test."""
    print("🧪 GIRA X1 CALLBACK ENDPOINT TEST")
    print("=" * 40)
    print(f"Target: {HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}")
    print(f"Token: {HOME_ASSISTANT_TOKEN[:20]}...")
    
    # Test both endpoints
    value_success = await test_single_callback(VALUE_CALLBACK_URL, "value")
    service_success = await test_single_callback(SERVICE_CALLBACK_URL, "service")
    
    print(f"\n📊 TEST RESULTS:")
    print(f"   Value callback:   {'✅ PASS' if value_success else '❌ FAIL'}")
    print(f"   Service callback: {'✅ PASS' if service_success else '❌ FAIL'}")
    
    if value_success and service_success:
        print(f"\n🎉 SUCCESS!")
        print(f"   Both callback endpoints are reachable from Gira X1's perspective")
        print(f"   Callback registration should work")
    else:
        print(f"\n❌ FAILURE!")
        print(f"   Gira X1 cannot reach one or more callback endpoints")
        print(f"   This explains why callback registration fails with 'callbackTestFailed'")
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Check if Home Assistant is running")
        print(f"   2. Verify Gira X1 integration is loaded")
        print(f"   3. Check firewall rules")
        print(f"   4. Verify network routing between devices")
    
    return value_success and service_success


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
