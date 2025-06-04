#!/usr/bin/env python3
"""
Comprehensive SSL/TLS callback endpoint test.

This test tries different SSL configurations to identify the exact issue
preventing Gira X1 from reaching Home Assistant callback endpoints.
"""

import asyncio
import aiohttp
import json
import ssl
import sys
import socket

# Configuration
HOME_ASSISTANT_IP = "10.1.1.242"
HOME_ASSISTANT_PORT = 8123
HOME_ASSISTANT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmOGYwZjM4NDk4ZjE0ZmZjODMwZmI0MTdlMWU1ZWRhYiIsImlhdCI6MTczMzI0ODQ3NSwiZXhwIjoyMDQ4NjA4NDc1fQ.3q2rZfBBwk9yP_WjlFN_2xHF7trnHbnJTLyEpFMN4Ao"

VALUE_CALLBACK_URL = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/value"


async def test_tcp_connectivity():
    """Test basic TCP connectivity without SSL."""
    print("🔌 Testing TCP connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((HOME_ASSISTANT_IP, HOME_ASSISTANT_PORT))
        sock.close()
        
        if result == 0:
            print("   ✅ TCP connection successful")
            return True
        else:
            print(f"   ❌ TCP connection failed: error code {result}")
            return False
    except Exception as e:
        print(f"   ❌ TCP test error: {e}")
        return False


async def test_ssl_configurations():
    """Test different SSL configurations."""
    print("\n🔐 Testing SSL configurations...")
    
    test_payload = {
        "uid": "test_ssl",
        "value": 1,
        "timestamp": "2025-06-04T10:30:00.000Z"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"
    }
    
    ssl_configs = [
        ("Default SSL", None),
        ("No SSL verification", ssl.create_default_context()),
        ("Legacy SSL", ssl.create_default_context()),
    ]
    
    # Configure SSL contexts
    ssl_configs[1] = ("No SSL verification", ssl.create_default_context())
    ssl_configs[1][1].check_hostname = False
    ssl_configs[1][1].verify_mode = ssl.CERT_NONE
    
    ssl_configs[2] = ("Legacy SSL", ssl.create_default_context())
    ssl_configs[2][1].check_hostname = False
    ssl_configs[2][1].verify_mode = ssl.CERT_NONE
    ssl_configs[2][1].set_ciphers('DEFAULT:@SECLEVEL=1')
    
    for config_name, ssl_context in ssl_configs:
        print(f"\n   Testing {config_name}...")
        
        try:
            if ssl_context is None:
                connector = aiohttp.TCPConnector()
            else:
                connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(VALUE_CALLBACK_URL, json=test_payload, headers=headers) as response:
                    print(f"   ✅ {config_name} SUCCESS: HTTP {response.status}")
                    response_text = await response.text()
                    print(f"      Response: {response_text[:100]}...")
                    return True
                    
        except aiohttp.ClientConnectorError as e:
            print(f"   ❌ {config_name} connection error: {e}")
        except asyncio.TimeoutError:
            print(f"   ❌ {config_name} timeout")
        except Exception as e:
            print(f"   ❌ {config_name} error: {e}")
    
    return False


async def test_http_fallback():
    """Test HTTP (non-HTTPS) connection."""
    print("\n🌐 Testing HTTP fallback...")
    
    http_url = f"http://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/value"
    print(f"   URL: {http_url}")
    
    test_payload = {
        "uid": "test_http",
        "value": 1,
        "timestamp": "2025-06-04T10:30:00.000Z"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(http_url, json=test_payload, headers=headers) as response:
                print(f"   ✅ HTTP SUCCESS: HTTP {response.status}")
                response_text = await response.text()
                print(f"      Response: {response_text[:100]}...")
                return True
                
    except aiohttp.ClientConnectorError as e:
        print(f"   ❌ HTTP connection error: {e}")
    except Exception as e:
        print(f"   ❌ HTTP error: {e}")
    
    return False


async def test_home_assistant_api():
    """Test basic Home Assistant API to verify it's running."""
    print("\n🏠 Testing Home Assistant API...")
    
    api_url = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/"
    headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
    
    # Try with no SSL verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(api_url, headers=headers) as response:
                print(f"   ✅ Home Assistant API responsive: HTTP {response.status}")
                return True
                
    except Exception as e:
        print(f"   ❌ Home Assistant API error: {e}")
        return False


async def check_webhook_endpoints():
    """Check if webhook endpoints are registered."""
    print("\n📋 Checking webhook endpoint registration...")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
    
    try:
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Test with GET (should return 405 if endpoint exists)
            async with session.get(VALUE_CALLBACK_URL, headers=headers) as response:
                print(f"   Value callback GET: HTTP {response.status}")
                if response.status == 405:
                    print("   ✅ Value callback endpoint exists (Method Not Allowed for GET)")
                    return True
                elif response.status == 404:
                    print("   ❌ Value callback endpoint not found")
                    return False
                else:
                    print(f"   ⚠️ Unexpected response: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Webhook check error: {e}")
        return False


async def main():
    """Run comprehensive connectivity tests."""
    print("🔍 COMPREHENSIVE CALLBACK CONNECTIVITY TEST")
    print("=" * 50)
    print(f"Target: {HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}")
    
    results = {
        "tcp": await test_tcp_connectivity(),
        "ha_api": await test_home_assistant_api(),
        "webhooks": await check_webhook_endpoints(),
        "ssl": await test_ssl_configurations(),
        "http": await test_http_fallback(),
    }
    
    print(f"\n📊 COMPREHENSIVE TEST RESULTS:")
    print("=" * 50)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper():.<20} {status}")
    
    print(f"\n🔧 DIAGNOSIS:")
    if not results["tcp"]:
        print("❌ No basic TCP connectivity - network routing issue")
    elif not results["ha_api"]:
        print("❌ Home Assistant not responding - service down or wrong IP/port")
    elif not results["webhooks"]:
        print("❌ Webhook endpoints not registered - integration not loaded properly")
    elif not results["ssl"] and not results["http"]:
        print("❌ SSL/TLS configuration issue - certificates or protocol mismatch")
        print("💡 Gira X1 may require specific SSL configuration")
    elif results["http"] and not results["ssl"]:
        print("⚠️ HTTP works but HTTPS fails - SSL certificate issue")
        print("💡 Consider configuring proper SSL certificates for Home Assistant")
    elif results["ssl"]:
        print("✅ Connectivity works - check Gira X1 network configuration")
    
    print(f"\n💡 RECOMMENDATIONS:")
    if not results["ssl"]:
        print("1. Configure Home Assistant with proper SSL certificates")
        print("2. Or configure Gira X1 to accept self-signed certificates")
        print("3. Check Home Assistant's HTTPS configuration")
    if results["tcp"] and results["ha_api"] and results["webhooks"]:
        print("4. The callback endpoints are properly set up")
        print("5. Focus on SSL/TLS configuration between Gira X1 and Home Assistant")
    
    return all(results.values())


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
