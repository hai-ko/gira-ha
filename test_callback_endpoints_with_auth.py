#!/usr/bin/env python3
"""
Test callback endpoints with proper authentication.
"""

import json
import ssl
import urllib.request
import urllib.error

# Configuration
HOME_ASSISTANT_IP = "10.1.1.242"
HOME_ASSISTANT_PORT = 8123
HOME_ASSISTANT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJmOGYwZjM4NDk4ZjE0ZmZjODMwZmI0MTdlMWU1ZWRhYiIsImlhdCI6MTczMzI0ODQ3NSwiZXhwIjoyMDQ4NjA4NDc1fQ.3q2rZfBBwk9yP_WjlFN_2xHF7trnHbnJTLyEpFMN4Ao"

# Callback URLs
VALUE_CALLBACK_URL = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/value"
SERVICE_CALLBACK_URL = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/service"

def test_callback_endpoint(url, callback_type):
    """Test a callback endpoint."""
    print(f"\n🔔 Testing {callback_type} callback: {url}")
    
    # Test payload
    if callback_type == "value":
        payload = {
            "uid": "test_callback",
            "value": 1,
            "timestamp": "2025-06-04T10:30:00.000Z"
        }
    else:
        payload = {
            "service": "test",
            "event": "test",
            "timestamp": "2025-06-04T10:30:00.000Z"
        }
    
    data = json.dumps(payload).encode('utf-8')
    
    # Create request
    request = urllib.request.Request(url, data=data)
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", f"Bearer {HOME_ASSISTANT_TOKEN}")
    
    # Test with disabled SSL verification (like Gira X1 might need)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(request, context=ssl_context, timeout=10) as response:
            status = response.status
            response_text = response.read().decode('utf-8')
            print(f"   ✅ SUCCESS: HTTP {status}")
            print(f"   Response: {response_text[:100]}...")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP Error {e.code}: {e.reason}")
        try:
            error_response = e.read().decode('utf-8')
            print(f"   Error details: {error_response[:100]}...")
        except:
            pass
        return False
    except urllib.error.URLError as e:
        print(f"   ❌ URL Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_endpoint_existence(url, endpoint_name):
    """Test if endpoint exists using GET (should return 405 Method Not Allowed)."""
    print(f"\n📋 Testing {endpoint_name} endpoint existence...")
    
    request = urllib.request.Request(url)
    request.add_header("Authorization", f"Bearer {HOME_ASSISTANT_TOKEN}")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(request, context=ssl_context, timeout=10) as response:
            print(f"   Unexpected success: HTTP {response.status}")
            return True
    except urllib.error.HTTPError as e:
        if e.code == 405:  # Method Not Allowed
            print(f"   ✅ Endpoint exists (405 Method Not Allowed for GET)")
            return True
        elif e.code == 404:
            print(f"   ❌ Endpoint not found (404)")
            return False
        else:
            print(f"   ⚠️ Unexpected status: {e.code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Test callback endpoints."""
    print("🔔 CALLBACK ENDPOINT TEST WITH AUTHENTICATION")
    print("=" * 50)
    print(f"Target: {HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}")
    print(f"Token: {HOME_ASSISTANT_TOKEN[:20]}...")
    
    # Test endpoint existence first
    value_exists = test_endpoint_existence(VALUE_CALLBACK_URL, "value")
    service_exists = test_endpoint_existence(SERVICE_CALLBACK_URL, "service")
    
    if not value_exists or not service_exists:
        print(f"\n❌ CRITICAL: Callback endpoints not registered!")
        print(f"   This means the Gira X1 integration webhook setup failed")
        return False
    
    # Test actual callback functionality
    value_works = test_callback_endpoint(VALUE_CALLBACK_URL, "value")
    service_works = test_callback_endpoint(SERVICE_CALLBACK_URL, "service")
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"Value endpoint exists:  {'✅' if value_exists else '❌'}")
    print(f"Service endpoint exists: {'✅' if service_exists else '❌'}")
    print(f"Value callback works:    {'✅' if value_works else '❌'}")
    print(f"Service callback works:  {'✅' if service_works else '❌'}")
    
    if value_works and service_works:
        print(f"\n🎉 SUCCESS!")
        print(f"   Callback endpoints are working correctly")
        print(f"   The issue may be specific to Gira X1's SSL configuration")
    else:
        print(f"\n❌ ISSUES FOUND:")
        if not value_exists or not service_exists:
            print(f"   - Webhook endpoints not properly registered")
        if value_exists and service_exists and (not value_works or not service_works):
            print(f"   - Endpoints exist but callback processing failed")
            print(f"   - Check Home Assistant logs for webhook errors")
    
    return value_works and service_works

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
