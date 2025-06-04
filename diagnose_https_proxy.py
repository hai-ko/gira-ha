#!/usr/bin/env python3
"""
Diagnose HTTPS Proxy Callback Issues

This script tests the HTTPS proxy connectivity from multiple perspectives
to understand why Gira X1 cannot reach the callback URLs.
"""

import requests
import socket
import subprocess
import json
from urllib.parse import urlparse

def test_proxy_basic_connectivity():
    """Test basic connectivity to the HTTPS proxy."""
    print("🔗 Testing HTTPS proxy basic connectivity...")
    
    try:
        response = requests.get(
            "https://home.hf17-1.de", 
            timeout=5,
            verify=False  # In case of SSL issues
        )
        print(f"   ✅ HTTPS proxy responds: HTTP {response.status_code}")
        return True
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_proxy_callback_endpoints():
    """Test the specific callback endpoints through the proxy."""
    print("\n📋 Testing HTTPS proxy callback endpoints...")
    
    endpoints = [
        "/api/gira_x1/callback/value",
        "/api/gira_x1/callback/service"
    ]
    
    for endpoint in endpoints:
        url = f"https://home.hf17-1.de{endpoint}"
        try:
            print(f"   Testing: {url}")
            response = requests.get(url, timeout=5, verify=False)
            print(f"   Response: HTTP {response.status_code}")
            
            # Check if it's forwarding to Home Assistant
            if response.status_code in [404, 401, 403]:
                print(f"   ✅ Proxy forwarding (expected auth/not found response)")
            elif response.status_code == 200:
                print(f"   ✅ Proxy working")
            else:
                print(f"   ⚠️  Unexpected response code")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_dns_resolution():
    """Test DNS resolution for the proxy domain."""
    print("\n🔍 Testing DNS resolution...")
    
    try:
        ip = socket.gethostbyname("home.hf17-1.de")
        print(f"   ✅ home.hf17-1.de resolves to: {ip}")
        
        # Test if we can reach that IP
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, 443))
            sock.close()
            
            if result == 0:
                print(f"   ✅ Port 443 reachable on {ip}")
            else:
                print(f"   ❌ Port 443 not reachable on {ip}")
                
        except Exception as e:
            print(f"   ❌ Socket test error: {e}")
            
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")

def test_from_gira_perspective():
    """Test connectivity from Gira X1's perspective."""
    print("\n🏠 Testing from Gira X1 network perspective...")
    
    # Try to ping from the same network segment
    gira_ip = "10.1.1.85"
    
    print(f"   Gira X1 IP: {gira_ip}")
    
    # Test if Gira can reach external internet
    try:
        # Try to ping a known external service from local network
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "3000", "8.8.8.8"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("   ✅ External internet connectivity available")
        else:
            print("   ❌ No external internet connectivity")
            print(f"   Ping output: {result.stdout}")
            
    except Exception as e:
        print(f"   ❌ Network test error: {e}")

def test_proxy_configuration():
    """Check proxy configuration details."""
    print("\n⚙️  Analyzing proxy configuration...")
    
    # Check what the proxy URL should be forwarding to
    home_assistant_ip = "10.1.1.242"
    home_assistant_port = "8123"
    
    print(f"   Expected target: https://{home_assistant_ip}:{home_assistant_port}")
    
    # Test direct connectivity to Home Assistant
    try:
        direct_url = f"http://{home_assistant_ip}:{home_assistant_port}/api/"
        response = requests.get(direct_url, timeout=5)
        print(f"   ✅ Direct HA connectivity: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ❌ Direct HA connectivity failed: {e}")

def main():
    """Main diagnostic function."""
    print("🔧 HTTPS Proxy Callback Diagnostic")
    print("===================================")
    print()
    print("Analyzing why Gira X1 cannot reach https://home.hf17-1.de callback URLs...")
    print()
    
    test_proxy_basic_connectivity()
    test_proxy_callback_endpoints()
    test_dns_resolution()
    test_from_gira_perspective()
    test_proxy_configuration()
    
    print("\n📊 ANALYSIS:")
    print("=" * 50)
    print("1. If proxy basic connectivity fails:")
    print("   → Proxy server may be down or misconfigured")
    print()
    print("2. If DNS resolution fails:")
    print("   → Domain not properly configured")
    print()
    print("3. If callback endpoints return errors:")
    print("   → Proxy not properly forwarding to Home Assistant")
    print()
    print("4. Expected proxy behavior:")
    print("   → https://home.hf17-1.de/api/gira_x1/callback/value")
    print("   → Should forward to: https://10.1.1.242:8123/api/gira_x1/callback/value")
    print()
    print("🔧 NEXT STEPS:")
    print("- Verify proxy server configuration")
    print("- Check proxy forwarding rules")
    print("- Ensure Gira X1 can reach external internet")
    print("- Consider network firewall rules")

if __name__ == "__main__":
    main()
