#!/usr/bin/env python3
"""
Test HTTPS Proxy Configuration

This script simulates what Gira X1 would do - send a callback to the proxy
to test if it properly forwards to Home Assistant.
"""

import socket
import ssl
import json
import time

def simulate_gira_callback(host, endpoint, callback_data):
    """Simulate a Gira X1 callback POST request."""
    print(f"📞 Simulating Gira X1 callback to: https://{host}{endpoint}")
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Prepare callback data (typical Gira X1 format)
        json_data = json.dumps(callback_data)
        content_length = len(json_data.encode('utf-8'))
        
        # Create HTTP POST request
        request = f"""POST {endpoint} HTTP/1.1\r
Host: {host}\r
Content-Type: application/json\r
Content-Length: {content_length}\r
User-Agent: Gira-X1-Client/1.0\r
Connection: close\r
\r
{json_data}"""
        
        print(f"📤 Sending callback data: {json_data}")
        
        # Connect and send request
        with socket.create_connection((host, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                ssock.send(request.encode())
                
                # Read response
                response = b""
                while True:
                    try:
                        data = ssock.recv(1024)
                        if not data:
                            break
                        response += data
                        if len(response) > 4096:
                            break
                    except socket.timeout:
                        break
                
                response_str = response.decode('utf-8', errors='ignore')
                
                # Parse response
                if response_str.startswith('HTTP/'):
                    lines = response_str.split('\r\n')
                    status_line = lines[0]
                    status_code = status_line.split()[1] if len(status_line.split()) > 1 else "unknown"
                    
                    print(f"📥 Response: {status_line}")
                    
                    # Analyze response
                    if status_code == '200':
                        print(f"   ✅ Callback successful - proxy forwarded to Home Assistant")
                        return True
                    elif status_code == '404':
                        print(f"   ❌ 404 Not Found - proxy not forwarding callback endpoints")
                        print(f"   💡 Proxy needs to be configured to forward {endpoint}")
                        return False
                    elif status_code == '401':
                        print(f"   ⚠️  401 Unauthorized - proxy forwarded but authentication required")
                        print(f"   💡 This suggests proxy is working but needs auth configuration")
                        return True  # Proxy is working, just needs auth
                    elif status_code.startswith('5'):
                        print(f"   ❌ Server error - proxy or Home Assistant issue")
                        return False
                    else:
                        print(f"   ⚠️  Unexpected response: {status_code}")
                        return False
                else:
                    print(f"   ❌ Invalid HTTP response")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Callback simulation failed: {e}")
        return False

def test_proxy_forwarding():
    """Test if proxy properly forwards to Home Assistant."""
    print("🔧 Testing HTTPS Proxy Forwarding Configuration")
    print("=" * 50)
    print()
    
    host = "home.hf17-1.de"
    
    # Test value callback endpoint
    value_callback_data = {
        "uid": "test-datapoint-123",
        "value": True,
        "timestamp": int(time.time() * 1000)
    }
    
    print("1️⃣ Testing value callback forwarding:")
    value_success = simulate_gira_callback(host, "/api/gira_x1/callback/value", value_callback_data)
    print()
    
    # Test service callback endpoint  
    service_callback_data = {
        "event": "test-event",
        "data": {"test": "value"},
        "timestamp": int(time.time() * 1000)
    }
    
    print("2️⃣ Testing service callback forwarding:")
    service_success = simulate_gira_callback(host, "/api/gira_x1/callback/service", service_callback_data)
    print()
    
    return value_success and service_success

def test_direct_home_assistant():
    """Test direct connection to Home Assistant for comparison."""
    print("🏠 Testing direct Home Assistant connectivity:")
    
    ha_ip = "10.1.1.242"
    ha_port = 8123
    
    try:
        # Test basic connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ha_ip, ha_port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Home Assistant reachable at {ha_ip}:{ha_port}")
        else:
            print(f"   ❌ Home Assistant not reachable at {ha_ip}:{ha_port}")
            
    except Exception as e:
        print(f"   ❌ Direct HA test error: {e}")

def main():
    """Main test function."""
    print("🔧 HTTPS Proxy Configuration Test")
    print("=================================")
    print()
    print("This test simulates what Gira X1 does when sending callbacks")
    print("to check if the proxy properly forwards to Home Assistant.")
    print()
    
    # Test proxy forwarding
    proxy_working = test_proxy_forwarding()
    print()
    
    # Test direct HA connectivity
    test_direct_home_assistant()
    print()
    
    print("📊 ANALYSIS:")
    print("=" * 30)
    
    if proxy_working:
        print("✅ PROXY WORKING: Callbacks are being forwarded correctly")
        print("🎯 NEXT: Check Home Assistant webhook handler registration")
    else:
        print("❌ PROXY ISSUE: Callbacks are not being forwarded")
        print("🔧 REQUIRED: Configure proxy to forward:")
        print("   /api/gira_x1/callback/value  → https://10.1.1.242:8123/api/gira_x1/callback/value")
        print("   /api/gira_x1/callback/service → https://10.1.1.242:8123/api/gira_x1/callback/service")
        print()
        print("💡 PROXY CONFIGURATION NEEDED:")
        print("   - Add reverse proxy rules for /api/gira_x1/callback/*")
        print("   - Forward to Home Assistant backend")
        print("   - Preserve headers and body")
        print("   - Handle SSL termination")

if __name__ == "__main__":
    main()
