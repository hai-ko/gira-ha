#!/usr/bin/env python3
"""
Verify SSL Termination Setup

This script verifies that the Home Assistant integration is properly configured
to receive HTTP requests from the HTTPS proxy after SSL termination.
"""

import requests
import json

# Configuration
HOMEASSISTANT_IP = "10.1.1.242"
HOMEASSISTANT_PORT = 8123
HOME_ASSISTANT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmOGYwZjM4NDk4ZjE0ZmZjODMwZmI0MTdlMWU1ZWRhYiIsImlhdCI6MTczMzI0ODQ3NSwiZXhwIjoyMDQ4NjA4NDc1fQ.3q2rZfBBwk9yP_WjlFN_2xHF7trnHbnJTLyEpFMN4Ao"

def test_http_callback_endpoint_direct():
    """Test that Home Assistant can receive HTTP callback requests directly."""
    print("🧪 Testing Home Assistant HTTP callback endpoint readiness...")
    print("   (This simulates what the proxy will send to Home Assistant)")
    
    # Test value callback endpoint via HTTP (as proxy would send)
    url = f"http://{HOMEASSISTANT_IP}:{HOMEASSISTANT_PORT}/api/gira_x1/callback/value"
    
    # Simulate a callback payload from Gira X1 (via proxy)
    test_payload = {
        "events": [
            {
                "uid": "ssl_termination_test",
                "value": True,
                "timestamp": "2025-01-19T10:30:00.000Z"
            }
        ],
        "test": True  # Mark as test event
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "HTTPS-Proxy/1.0",
        "X-Forwarded-For": "10.1.1.85",  # Simulate proxy headers
        "X-Forwarded-Proto": "https"
    }
    
    try:
        response = requests.post(
            url, 
            json=test_payload, 
            headers=headers, 
            timeout=10
        )
        
        print(f"   Response: HTTP {response.status_code}")
        print(f"   Response body: {response.text}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS: Home Assistant accepts HTTP requests from proxy")
            print("   📋 Integration is properly configured for SSL termination")
            return True
        elif response.status_code == 404:
            print("   ❌ FAIL: Callback endpoint not found")
            print("   💡 Check that Gira X1 integration is loaded in Home Assistant")
            return False
        else:
            print(f"   ⚠️ UNEXPECTED: Received HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ CONNECTION ERROR: {e}")
        print("   💡 Check that Home Assistant is running and accessible")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def test_service_callback_endpoint():
    """Test service callback endpoint."""
    print("\n🧪 Testing service callback endpoint...")
    
    url = f"http://{HOMEASSISTANT_IP}:{HOMEASSISTANT_PORT}/api/gira_x1/callback/service"
    
    test_payload = {
        "service": "test_service",
        "event": "ssl_termination_test",
        "timestamp": "2025-01-19T10:30:00.000Z",
        "test": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "HTTPS-Proxy/1.0"
    }
    
    try:
        response = requests.post(url, json=test_payload, headers=headers, timeout=10)
        
        print(f"   Response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS: Service callback endpoint ready")
            return True
        elif response.status_code == 404:
            print("   ❌ FAIL: Service callback endpoint not found")
            return False
        else:
            print(f"   ⚠️ UNEXPECTED: Received HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def check_integration_configuration():
    """Check that integration is configured to use HTTPS proxy."""
    print("\n🔍 Checking integration configuration...")
    
    try:
        with open('/Users/heikoburkhardt/repos/gira-x1-ha/custom_components/gira_x1/__init__.py', 'r') as f:
            content = f.read()
        
        if 'https://home.hf17-1.de' in content:
            print("   ✅ HTTPS proxy URL configured in integration")
        else:
            print("   ❌ HTTPS proxy URL not found in integration")
            return False
            
        if 'SSL termination' in content:
            print("   ✅ SSL termination setup documented in code")
        else:
            print("   ⚠️ SSL termination setup not documented")
            
        if 'requires_auth = False' in content:
            print("   ✅ Webhook handlers configured for proxy forwarding")
        else:
            # Check webhook.py
            try:
                with open('/Users/heikoburkhardt/repos/gira-x1-ha/custom_components/gira_x1/webhook.py', 'r') as f:
                    webhook_content = f.read()
                if 'requires_auth = False' in webhook_content:
                    print("   ✅ Webhook handlers configured for proxy forwarding")
                else:
                    print("   ❌ Webhook handlers may require authentication")
                    return False
            except:
                print("   ⚠️ Could not check webhook configuration")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR checking configuration: {e}")
        return False

def main():
    """Main test function."""
    print("🔧 SSL TERMINATION SETUP VERIFICATION")
    print("=" * 50)
    print("Testing if Home Assistant is ready to receive HTTP requests from HTTPS proxy")
    print()
    
    # Test integration configuration
    config_ok = check_integration_configuration()
    
    # Test HTTP callback endpoints
    value_ok = test_http_callback_endpoint_direct()
    service_ok = test_service_callback_endpoint()
    
    print("\n📊 VERIFICATION RESULTS:")
    print("=" * 30)
    print(f"Integration Config:  {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"Value Callback:      {'✅ PASS' if value_ok else '❌ FAIL'}")
    print(f"Service Callback:    {'✅ PASS' if service_ok else '❌ FAIL'}")
    
    if config_ok and value_ok and service_ok:
        print("\n🎉 SUCCESS!")
        print("Home Assistant is properly configured for SSL termination.")
        print()
        print("💡 NEXT STEPS:")
        print("1. Configure your proxy server to forward:")
        print("   /api/gira_x1/callback/* → http://10.1.1.242:8123/api/gira_x1/callback/*")
        print("2. Test the complete flow: Gira X1 → HTTPS Proxy → HTTP Home Assistant")
        print()
        print("🔄 EXPECTED FLOW:")
        print("Gira X1 → HTTPS → https://home.hf17-1.de/api/gira_x1/callback/value")
        print("Proxy   → HTTP  → http://10.1.1.242:8123/api/gira_x1/callback/value")
        print("HA      ← 200   ← Webhook handler processes request")
        
    else:
        print("\n❌ ISSUES DETECTED")
        print("Some components are not ready for SSL termination setup.")
        if not config_ok:
            print("- Fix integration configuration")
        if not value_ok:
            print("- Check Gira X1 integration is loaded and value callback is registered")
        if not service_ok:
            print("- Check service callback registration")

if __name__ == "__main__":
    main()
