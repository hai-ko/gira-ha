#!/usr/bin/env python3
"""
Test HTTPS Proxy with SSL Termination Setup

This script validates the complete proxy setup:
1. Gira X1 → HTTPS → https://home.hf17-1.de
2. Proxy → HTTP → http://10.1.1.242:8123 
3. Home Assistant webhook handlers ready for HTTP requests
"""

import socket
import ssl
import json
import time
import subprocess

def test_gira_to_proxy():
    """Test the first part: Gira X1 → HTTPS → Proxy"""
    print("1️⃣ Testing Gira X1 → HTTPS → Proxy")
    print("   Testing: https://home.hf17-1.de/api/gira_x1/callback/value")
    
    host = "home.hf17-1.de"
    endpoint = "/api/gira_x1/callback/value"
    
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Simulate Gira X1 callback
        callback_data = {
            "uid": "test-123",
            "value": True,
            "timestamp": int(time.time() * 1000)
        }
        
        json_data = json.dumps(callback_data)
        content_length = len(json_data.encode('utf-8'))
        
        request = f"""POST {endpoint} HTTP/1.1\r
Host: {host}\r
Content-Type: application/json\r
Content-Length: {content_length}\r
User-Agent: Gira-X1-Test/1.0\r
Connection: close\r
\r
{json_data}"""
        
        with socket.create_connection((host, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                ssock.send(request.encode())
                
                response = b""
                while True:
                    try:
                        data = ssock.recv(1024)
                        if not data:
                            break
                        response += data
                        if len(response) > 2048:
                            break
                    except socket.timeout:
                        break
                
                response_str = response.decode('utf-8', errors='ignore')
                
                if response_str.startswith('HTTP/'):
                    status_line = response_str.split('\r\n')[0]
                    status_code = status_line.split()[1] if len(status_line.split()) > 1 else "unknown"
                    
                    print(f"   ✅ HTTPS request successful: {status_code}")
                    
                    if status_code == '200':
                        print(f"   ✅ Proxy forwarding working!")
                        return True
                    elif status_code in ['401', '403']:
                        print(f"   ✅ Proxy forwarding (auth required)")
                        return True
                    elif status_code == '404':
                        print(f"   ⚠️  Proxy not configured for this endpoint")
                        return False
                    else:
                        print(f"   ⚠️  Unexpected response: {status_code}")
                        return False
                        
    except Exception as e:
        print(f"   ❌ HTTPS test failed: {e}")
        return False

def test_proxy_to_homeassistant():
    """Test the second part: Proxy → HTTP → Home Assistant"""
    print("\n2️⃣ Testing Proxy → HTTP → Home Assistant")
    print("   Testing: http://10.1.1.242:8123/api/gira_x1/callback/value")
    
    ha_ip = "10.1.1.242"
    ha_port = 8123
    endpoint = "/api/gira_x1/callback/value"
    
    try:
        # Test HTTP connection to Home Assistant
        callback_data = {
            "uid": "test-456", 
            "value": False,
            "timestamp": int(time.time() * 1000)
        }
        
        json_data = json.dumps(callback_data)
        content_length = len(json_data.encode('utf-8'))
        
        request = f"""POST {endpoint} HTTP/1.1\r
Host: {ha_ip}:{ha_port}\r
Content-Type: application/json\r
Content-Length: {content_length}\r
User-Agent: Proxy-Test/1.0\r
Connection: close\r
\r
{json_data}"""
        
        with socket.create_connection((ha_ip, ha_port), timeout=10) as sock:
            sock.send(request.encode())
            
            response = b""
            while True:
                try:
                    data = sock.recv(1024)
                    if not data:
                        break
                    response += data
                    if len(response) > 2048:
                        break
                except socket.timeout:
                    break
            
            response_str = response.decode('utf-8', errors='ignore')
            
            if response_str.startswith('HTTP/'):
                status_line = response_str.split('\r\n')[0]
                status_code = status_line.split()[1] if len(status_line.split()) > 1 else "unknown"
                
                print(f"   ✅ HTTP request successful: {status_code}")
                
                if status_code == '200':
                    print(f"   ✅ Home Assistant webhook responding!")
                    return True
                elif status_code == '404':
                    print(f"   ⚠️  Webhook not registered yet")
                    return False
                elif status_code in ['401', '403']:
                    print(f"   ⚠️  Authentication issue")
                    return False
                else:
                    print(f"   ⚠️  Unexpected response: {status_code}")
                    return False
            else:
                print(f"   ❌ Invalid HTTP response")
                return False
                
    except Exception as e:
        print(f"   ❌ HTTP test failed: {e}")
        return False

def check_homeassistant_integration():
    """Check if Home Assistant integration is loaded correctly"""
    print("\n3️⃣ Checking Home Assistant Integration Status")
    
    try:
        # Check logs for recent integration activity
        result = subprocess.run(
            ["docker", "logs", "--tail", "20", "--since", "5m", "homeassistant"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            
            # Look for relevant lines
            callback_lines = [line for line in lines if 'CALLBACK' in line or 'gira_x1' in line]
            
            if callback_lines:
                print("   📋 Recent integration activity:")
                for line in callback_lines[-5:]:
                    print(f"      {line}")
                    
                # Check for specific patterns
                if any('HTTPS proxy with SSL termination' in line for line in callback_lines):
                    print("   ✅ Integration using correct proxy setup")
                    return True
                else:
                    print("   ⚠️  Integration may not be using proxy setup")
                    return False
            else:
                print("   ⚠️  No recent integration activity found")
                return False
        else:
            print(f"   ❌ Could not check logs: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Log check failed: {e}")
        return False

def main():
    """Main validation function."""
    print("🔧 HTTPS Proxy with SSL Termination Validation")
    print("=" * 50)
    print()
    print("Testing complete proxy chain:")
    print("Gira X1 → HTTPS → home.hf17-1.de → HTTP → 10.1.1.242:8123")
    print()
    
    # Test each part of the chain
    step1_ok = test_gira_to_proxy()
    step2_ok = test_proxy_to_homeassistant()
    step3_ok = check_homeassistant_integration()
    
    print("\n📊 VALIDATION RESULTS:")
    print("=" * 30)
    print(f"1️⃣ Gira X1 → Proxy (HTTPS):     {'✅ PASS' if step1_ok else '❌ FAIL'}")
    print(f"2️⃣ Proxy → Home Assistant (HTTP): {'✅ PASS' if step2_ok else '❌ FAIL'}")
    print(f"3️⃣ Integration Status:           {'✅ PASS' if step3_ok else '❌ FAIL'}")
    
    if step1_ok and step2_ok and step3_ok:
        print("\n🎉 SUCCESS: Complete proxy chain working!")
        print("✅ Gira X1 should be able to send callbacks successfully")
    elif step1_ok and step3_ok and not step2_ok:
        print("\n⚠️  PARTIAL: Proxy working, but Home Assistant webhook not ready")
        print("🔄 Try restarting Home Assistant to register webhooks")
    elif step1_ok and not step2_ok:
        print("\n❌ ISSUE: Proxy not forwarding to Home Assistant correctly")
        print("🔧 Check proxy configuration for HTTP forwarding")
    else:
        print("\n❌ ISSUE: Multiple problems detected")
        print("🔧 Check proxy setup and Home Assistant configuration")
    
    print("\n🎯 EXPECTED BEHAVIOR:")
    print("- Gira X1 sends HTTPS to https://home.hf17-1.de/api/gira_x1/callback/*")
    print("- Proxy terminates SSL and forwards HTTP to http://10.1.1.242:8123/api/gira_x1/callback/*")  
    print("- Home Assistant webhook handlers process HTTP requests")
    print("- Integration receives real-time updates")

if __name__ == "__main__":
    main()
