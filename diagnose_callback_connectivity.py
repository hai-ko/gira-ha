#!/usr/bin/env python3
"""
Network Connectivity Diagnostic for Gira X1 Callbacks
====================================================

This script diagnoses why Gira X1 cannot reach Home Assistant's callback endpoints.
The IP detection is working correctly (10.1.1.242), but network connectivity is failing.
"""

import asyncio
import aiohttp
import socket
import subprocess
import ssl
import json
from urllib.parse import urlparse

# Configuration
GIRA_X1_IP = "10.1.1.85"
HOME_ASSISTANT_IP = "10.1.1.242"
HOME_ASSISTANT_PORT = 8123
CALLBACK_PATHS = [
    "/api/gira_x1/callback/value",
    "/api/gira_x1/callback/service"
]

def test_basic_network_connectivity():
    """Test basic network connectivity between IPs."""
    print("🌐 TESTING BASIC NETWORK CONNECTIVITY")
    print("=" * 50)
    
    # Test if we can reach Gira X1
    print(f"📡 Testing connection to Gira X1 ({GIRA_X1_IP})...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((GIRA_X1_IP, 443))  # Gira X1 HTTPS port
        sock.close()
        
        if result == 0:
            print(f"✅ Can reach Gira X1 at {GIRA_X1_IP}:443")
        else:
            print(f"❌ Cannot reach Gira X1 at {GIRA_X1_IP}:443")
    except Exception as e:
        print(f"❌ Error testing Gira X1 connectivity: {e}")
    
    # Test if we can bind to Home Assistant port
    print(f"\n🏠 Testing Home Assistant port ({HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT})...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((HOME_ASSISTANT_IP, HOME_ASSISTANT_PORT))
        sock.close()
        
        if result == 0:
            print(f"✅ Home Assistant port {HOME_ASSISTANT_PORT} is accessible")
        else:
            print(f"❌ Cannot reach Home Assistant at {HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}")
            print(f"   This could mean:")
            print(f"   - Home Assistant is not listening on {HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}")
            print(f"   - Firewall is blocking the connection")
            print(f"   - Home Assistant is only listening on localhost (127.0.0.1)")
    except Exception as e:
        print(f"❌ Error testing Home Assistant connectivity: {e}")

def test_home_assistant_configuration():
    """Test Home Assistant network configuration."""
    print("\n🔧 TESTING HOME ASSISTANT CONFIGURATION")
    print("=" * 50)
    
    # Check what IP addresses are listening on port 8123
    try:
        print("📋 Checking what's listening on port 8123...")
        result = subprocess.run(
            ["lsof", "-i", f":{HOME_ASSISTANT_PORT}"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0 and result.stdout:
            print("✅ Found processes listening on port 8123:")
            for line in result.stdout.split('\n'):
                if 'LISTEN' in line:
                    print(f"   {line}")
        else:
            print("❌ No processes found listening on port 8123")
            print("   Home Assistant may not be running or configured incorrectly")
            
    except subprocess.TimeoutExpired:
        print("⚠️ Command timed out")
    except FileNotFoundError:
        print("⚠️ lsof command not found (macOS/Linux)")
    except Exception as e:
        print(f"❌ Error checking port: {e}")
    
    # Check network interfaces
    print(f"\n🌐 Checking if {HOME_ASSISTANT_IP} is configured on this machine...")
    try:
        result = subprocess.run(
            ["ifconfig"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            if HOME_ASSISTANT_IP in result.stdout:
                print(f"✅ IP {HOME_ASSISTANT_IP} is configured on this machine")
            else:
                print(f"❌ IP {HOME_ASSISTANT_IP} is NOT configured on this machine")
                print("   This could be the problem - Home Assistant may be running on a different IP")
                print("   Common Home Assistant IPs:")
                print("   - 127.0.0.1 (localhost only)")
                print("   - 0.0.0.0 (all interfaces)")
                print("   - 192.168.x.x (common home network range)")
                
                # Show available IPs
                print("\n📍 Available IP addresses on this machine:")
                for line in result.stdout.split('\n'):
                    if 'inet ' in line and 'inet 127' not in line:
                        ip_part = line.strip().split()
                        for i, part in enumerate(ip_part):
                            if part == 'inet' and i + 1 < len(ip_part):
                                ip = ip_part[i + 1]
                                print(f"   {ip}")
        else:
            print("❌ Could not check network interfaces")
            
    except Exception as e:
        print(f"❌ Error checking network interfaces: {e}")

async def test_callback_endpoints():
    """Test if callback endpoints are accessible via HTTPS."""
    print("\n📞 TESTING CALLBACK ENDPOINTS")
    print("=" * 50)
    
    # Create SSL context that accepts self-signed certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        for path in CALLBACK_PATHS:
            url = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}{path}"
            print(f"🔍 Testing: {url}")
            
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    print(f"✅ HTTP {response.status}: {url}")
                    if response.status == 200:
                        text = await response.text()
                        print(f"   Response: {text[:100]}...")
                    else:
                        print(f"   Unexpected status code: {response.status}")
                        
            except aiohttp.ClientConnectorError as e:
                print(f"❌ Connection failed: {url}")
                print(f"   Error: {e}")
                print(f"   This means Gira X1 would also fail to connect")
                
            except aiohttp.ServerTimeoutError:
                print(f"⚠️ Timeout: {url}")
                print(f"   Server took too long to respond")
                
            except Exception as e:
                print(f"❌ Error: {url}")
                print(f"   Error: {e}")

def test_firewall_configuration():
    """Test firewall configuration."""
    print("\n🛡️ TESTING FIREWALL CONFIGURATION")
    print("=" * 50)
    
    print("📋 Checking macOS firewall status...")
    try:
        # Check if macOS firewall is enabled
        result = subprocess.run(
            ["sudo", "pfctl", "-s", "info"],
            capture_output=True, text=True, timeout=10
        )
        
        if "Status: Enabled" in result.stdout:
            print("⚠️ pfctl firewall is enabled")
            print("   This could be blocking connections from Gira X1")
        else:
            print("✅ pfctl firewall appears to be disabled")
            
    except subprocess.TimeoutExpired:
        print("⚠️ Command timed out")
    except Exception as e:
        print(f"⚠️ Could not check firewall status: {e}")
    
    # Check macOS Application Firewall
    try:
        result = subprocess.run(
            ["/usr/libexec/ApplicationFirewall/socketfilterfw", "--getglobalstate"],
            capture_output=True, text=True, timeout=10
        )
        
        if "enabled" in result.stdout.lower():
            print("⚠️ macOS Application Firewall is enabled")
            print("   Home Assistant may need to be allowed through the firewall")
        else:
            print("✅ macOS Application Firewall appears to be disabled")
            
    except Exception as e:
        print(f"⚠️ Could not check Application Firewall: {e}")

def provide_solutions():
    """Provide solutions based on common issues."""
    print("\n🔧 POTENTIAL SOLUTIONS")
    print("=" * 50)
    
    print("Based on the 'Callback test failed' error, here are the most likely causes and solutions:")
    print()
    
    print("1. 🏠 HOME ASSISTANT HTTPS CONFIGURATION:")
    print("   - Gira X1 REQUIRES HTTPS for callbacks (not HTTP)")
    print("   - Check your Home Assistant configuration.yaml:")
    print("     http:")
    print("       ssl_certificate: /path/to/certificate.pem")
    print("       ssl_key: /path/to/private.key")
    print("   - Or use a self-signed certificate:")
    print("     openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes")
    print()
    
    print("2. 🌐 NETWORK BINDING:")
    print("   - Home Assistant might be listening only on 127.0.0.1 (localhost)")
    print("   - Configure Home Assistant to listen on all interfaces:")
    print("     http:")
    print(f"       server_host: 0.0.0.0  # or specifically {HOME_ASSISTANT_IP}")
    print(f"       server_port: {HOME_ASSISTANT_PORT}")
    print()
    
    print("3. 🛡️ FIREWALL CONFIGURATION:")
    print("   - Allow incoming connections on port 8123:")
    print("     sudo ufw allow 8123  # Ubuntu/Linux")
    print("     # macOS: System Preferences > Security & Privacy > Firewall > Options")
    print(f"   - Allow traffic from {GIRA_X1_IP} to {HOME_ASSISTANT_IP}:8123")
    print()
    
    print("4. 🔍 ROUTER/NETWORK CONFIGURATION:")
    print("   - Ensure both devices are on the same network segment")
    print("   - Check if there's a VLAN or network isolation")
    print("   - Test ping between devices:")
    print(f"     ping {GIRA_X1_IP}  # from Home Assistant machine")
    print()
    
    print("5. 📞 TEST CALLBACK MANUALLY:")
    print("   - You can test the exact callback Gira X1 is trying to make:")
    print(f"     curl -k -X POST https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/gira_x1/callback/value \\")
    print(f"          -H 'Content-Type: application/json' \\")
    print(f"          -d '{{\"events\": [{{\"event\": \"test\"}}]}}'")
    print("   - Expected response: 'Gira X1 Value Callback Endpoint'")

async def main():
    """Run all diagnostic tests."""
    print("🔍 GIRA X1 CALLBACK CONNECTIVITY DIAGNOSTIC")
    print("=" * 50)
    print(f"Gira X1 IP: {GIRA_X1_IP}")
    print(f"Home Assistant IP: {HOME_ASSISTANT_IP}")
    print(f"Home Assistant Port: {HOME_ASSISTANT_PORT}")
    print()
    
    # Run all tests
    test_basic_network_connectivity()
    test_home_assistant_configuration()
    await test_callback_endpoints()
    test_firewall_configuration()
    provide_solutions()
    
    print("\n" + "=" * 50)
    print("🎯 NEXT STEPS:")
    print("1. Fix any issues identified above")
    print("2. Restart Home Assistant")
    print("3. Check the integration logs again")
    print("4. If callbacks still fail, the integration will use 5-second polling (which works fine)")

if __name__ == "__main__":
    asyncio.run(main())
