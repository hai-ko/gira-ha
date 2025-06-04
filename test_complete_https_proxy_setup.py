#!/usr/bin/env python3
"""
Complete HTTPS proxy validation test for Gira X1 integration.

This script tests the entire callback workflow with the HTTPS proxy configuration:
1. Tests HTTPS proxy connectivity
2. Tests callback endpoint registration through proxy
3. Simulates Gira X1 callback test
4. Provides step-by-step guidance

Run this AFTER restarting Home Assistant with the updated integration.
"""

import asyncio
import aiohttp
import json
import sys
import time

# Configuration
HTTPS_PROXY_URL = "https://home.hf17-1.de"
LOCAL_IP = "10.1.1.242"
HOME_ASSISTANT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmOGYwZjM4NDk4ZjE0ZmZjODMwZmI0MTdlMWU1ZWRhYiIsImlhdCI6MTczMzI0ODQ3NSwiZXhwIjoyMDQ4NjA4NDc1fQ.3q2rZfBBwk9yP_WjlFN_2xHF7trnHbnJTLyEpFMN4Ao"

# Callback URLs
PROXY_VALUE_URL = f"{HTTPS_PROXY_URL}/api/gira_x1/callback/value"
PROXY_SERVICE_URL = f"{HTTPS_PROXY_URL}/api/gira_x1/callback/service"
LOCAL_VALUE_URL = f"https://{LOCAL_IP}:8123/api/gira_x1/callback/value"
LOCAL_SERVICE_URL = f"https://{LOCAL_IP}:8123/api/gira_x1/callback/service"


async def test_https_proxy_basic():
    """Test basic HTTPS proxy connectivity."""
    print("🌐 Step 1: Testing HTTPS proxy basic connectivity...")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            api_url = f"{HTTPS_PROXY_URL}/api/"
            headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
            
            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    print("   ✅ HTTPS proxy working - Home Assistant API accessible")
                    return True
                elif response.status == 401:
                    print("   ✅ HTTPS proxy working - Home Assistant responding (401 expected for wrong token)")
                    return True
                else:
                    print(f"   ⚠️ HTTPS proxy responds but unexpected status: {response.status}")
                    return True
                    
    except Exception as e:
        print(f"   ❌ HTTPS proxy connection failed: {e}")
        return False


async def test_webhook_registration_proxy():
    """Test if webhook endpoints are registered and accessible through proxy."""
    print("\n📋 Step 2: Testing webhook endpoint registration through proxy...")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test value callback endpoint
            async with session.get(PROXY_VALUE_URL, headers=headers) as response:
                value_status = response.status
                print(f"   Value callback (GET): HTTP {value_status}")
                
            # Test service callback endpoint
            async with session.get(PROXY_SERVICE_URL, headers=headers) as response:
                service_status = response.status
                print(f"   Service callback (GET): HTTP {service_status}")
            
            if value_status == 405 and service_status == 405:
                print("   ✅ Both webhook endpoints registered through proxy (405 = Method Not Allowed for GET)")
                return True
            elif value_status == 404 or service_status == 404:
                print("   ❌ Webhook endpoints not found (404) - integration not loaded or not using proxy")
                return False
            else:
                print(f"   ⚠️ Unexpected status codes - may indicate partial setup")
                return False
                
    except Exception as e:
        print(f"   ❌ Webhook registration test failed: {e}")
        return False


async def test_webhook_registration_local():
    """Test if webhook endpoints are still registered locally (fallback)."""
    print("\n📋 Step 2b: Testing webhook endpoint registration on local IP...")
    
    try:
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=10)
        headers = {"Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"}
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Test value callback endpoint
            async with session.get(LOCAL_VALUE_URL, headers=headers) as response:
                value_status = response.status
                print(f"   Local value callback (GET): HTTP {value_status}")
                
            # Test service callback endpoint
            async with session.get(LOCAL_SERVICE_URL, headers=headers) as response:
                service_status = response.status
                print(f"   Local service callback (GET): HTTP {service_status}")
            
            if value_status == 405 and service_status == 405:
                print("   ✅ Webhook endpoints registered locally (fallback working)")
                return True
            else:
                print("   ❌ Local webhook endpoints also not working")
                return False
                
    except Exception as e:
        print(f"   ❌ Local webhook test failed: {e}")
        return False


async def simulate_gira_callback_test_proxy():
    """Simulate Gira X1 callback test through proxy."""
    print("\n🧪 Step 3: Simulating Gira X1 callback test through proxy...")
    
    test_payload = {
        "uid": "test_gira_callback_proxy",
        "value": 1,
        "timestamp": "2025-06-04T10:30:00.000Z"
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Gira-X1-Test",
        "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}"
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(PROXY_VALUE_URL, json=test_payload, headers=headers) as response:
                status = response.status
                response_text = await response.text()
                
                print(f"   Callback test status: HTTP {status}")
                print(f"   Response: {response_text[:100]}...")
                
                if 200 <= status < 300:
                    print("   ✅ Gira X1 callback test would SUCCEED through proxy")
                    return True
                else:
                    print("   ❌ Gira X1 callback test would FAIL through proxy")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Callback simulation failed: {e}")
        return False


async def check_integration_logs():
    """Check if integration is using proxy URLs in logs."""
    print("\n📝 Step 4: Integration log guidance...")
    print("   After restarting Home Assistant, check the logs for:")
    print("   ✅ '🌐 CALLBACK URL: Using HTTPS proxy - https://home.hf17-1.de'")
    print("   ✅ '💡 HTTPS PROXY: This should resolve SSL/TLS connectivity issues'")
    print("   ✅ '📞 CALLBACK REGISTRATION: Starting callback registration with Gira X1'")
    print("   ✅ '✅ CALLBACK REGISTRATION SUCCESS: Callbacks registered successfully'")
    print("\n   To check logs:")
    print("   docker logs homeassistant | grep -i gira")
    print("   or check Home Assistant UI > Settings > System > Logs")


def print_setup_instructions():
    """Print setup instructions."""
    print("\n🔧 SETUP INSTRUCTIONS:")
    print("=" * 50)
    print("1. 🔄 RESTART Home Assistant to load updated integration")
    print("2. 🔍 CHECK logs for proxy usage confirmation")
    print("3. 🧪 RUN this test again to verify webhook registration")
    print("4. 📞 TEST Gira X1 callback registration")
    print("\nAfter restart, you should see:")
    print("- Integration using HTTPS proxy URLs")
    print("- Successful webhook registration through proxy")
    print("- Gira X1 callback test passing")


async def main():
    """Run complete HTTPS proxy validation."""
    print("🔗 COMPLETE HTTPS PROXY VALIDATION FOR GIRA X1")
    print("=" * 55)
    print(f"HTTPS Proxy: {HTTPS_PROXY_URL}")
    print(f"Local IP: {LOCAL_IP}")
    print(f"Testing at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Basic proxy connectivity
    proxy_basic = await test_https_proxy_basic()
    
    # Step 2: Webhook registration
    webhook_proxy = await test_webhook_registration_proxy()
    webhook_local = False
    
    if not webhook_proxy:
        webhook_local = await test_webhook_registration_local()
    
    # Step 3: Callback simulation (only if webhooks are working)
    callback_success = False
    if webhook_proxy:
        callback_success = await simulate_gira_callback_test_proxy()
    
    # Step 4: Log guidance
    await check_integration_logs()
    
    # Results summary
    print(f"\n📊 VALIDATION RESULTS:")
    print("=" * 30)
    print(f"HTTPS Proxy Basic:      {'✅ PASS' if proxy_basic else '❌ FAIL'}")
    print(f"Webhooks via Proxy:     {'✅ PASS' if webhook_proxy else '❌ FAIL'}")
    print(f"Webhooks via Local:     {'✅ PASS' if webhook_local else '❌ FAIL'}")
    print(f"Callback Simulation:    {'✅ PASS' if callback_success else '❌ FAIL'}")
    
    # Diagnosis and next steps
    if proxy_basic and webhook_proxy and callback_success:
        print(f"\n🎉 COMPLETE SUCCESS!")
        print(f"   ✅ HTTPS proxy is working perfectly")
        print(f"   ✅ Webhook endpoints accessible through proxy")
        print(f"   ✅ Gira X1 callback registration should work")
        print(f"\n💡 READY FOR PRODUCTION:")
        print(f"   - Gira X1 can now register callbacks successfully")
        print(f"   - Real-time updates should work")
        print(f"   - No more SSL/TLS connectivity issues")
        
    elif proxy_basic and webhook_local and not webhook_proxy:
        print(f"\n⚠️ PARTIAL SUCCESS - NEEDS RESTART:")
        print(f"   ✅ HTTPS proxy connectivity works")
        print(f"   ✅ Integration works locally (fallback)")
        print(f"   ❌ Webhooks not yet registered through proxy")
        print(f"\n🔄 ACTION REQUIRED:")
        print(f"   1. RESTART Home Assistant to load updated integration")
        print(f"   2. Integration should then use proxy URLs")
        print(f"   3. Run this test again to confirm")
        
    elif proxy_basic and not webhook_proxy and not webhook_local:
        print(f"\n❌ INTEGRATION ISSUE:")
        print(f"   ✅ HTTPS proxy connectivity works")
        print(f"   ❌ Gira X1 integration not loaded or configured")
        print(f"\n🔧 TROUBLESHOOTING:")
        print(f"   1. Check if Gira X1 integration is enabled")
        print(f"   2. Verify integration configuration")
        print(f"   3. Check Home Assistant logs for errors")
        
    else:
        print(f"\n❌ CONNECTIVITY ISSUE:")
        print(f"   ❌ HTTPS proxy not accessible")
        print(f"\n🔧 TROUBLESHOOTING:")
        print(f"   1. Check proxy configuration")
        print(f"   2. Verify network connectivity")
        print(f"   3. Test proxy URL manually")
    
    # Always show setup instructions
    print_setup_instructions()
    
    return proxy_basic and (webhook_proxy or webhook_local)


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
