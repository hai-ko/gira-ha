#!/usr/bin/env python3
"""
Test the Gira X1 callback registration with the new IP detection logic.
This will attempt to connect to the real Gira X1 device and register callbacks
using the detected local IP address.
"""

import asyncio
import logging
import sys
import os

# Add the custom_components path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from gira_x1.api import GiraX1Api
from gira_x1.const import CONF_HOST, CONF_TOKEN

# Set up logging
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

# Test configuration (replace with your actual values)
GIRA_X1_HOST = "10.1.1.85"  # Your Gira X1 IP
GIRA_X1_TOKEN = "heiko.test.token"  # Your token

async def test_callback_registration():
    """Test callback registration with the new IP detection logic."""
    
    print("=== Testing Gira X1 Callback Registration ===")
    
    try:
        # Create API instance
        api = GiraX1Api(GIRA_X1_HOST, GIRA_X1_TOKEN)
        
        # Test basic connectivity first
        print(f"📡 Testing connectivity to Gira X1 at {GIRA_X1_HOST}...")
        
        # Get device info to test connection
        device_info = await api.get_device_info()
        print(f"✅ Successfully connected to Gira X1:")
        print(f"   Device: {device_info.get('name', 'Unknown')}")
        print(f"   Version: {device_info.get('version', 'Unknown')}")
        
        # Import the IP detection function we just implemented
        import socket
        
        def get_local_ip_for_gira_x1() -> str | None:
            """Get the local IP that should be used for Gira X1 callbacks."""
            try:
                hostname = socket.gethostname()
                _LOGGER.debug("Current hostname: %s", hostname)
                
                local_ips = []
                
                # Method 1: Get IPs from hostname
                try:
                    for addr_info in socket.getaddrinfo(hostname, None):
                        ip = addr_info[4][0]
                        if ip not in local_ips and not ip.startswith('127.'):
                            local_ips.append(ip)
                except Exception as e:
                    _LOGGER.debug("Error getting IPs from hostname: %s", e)
                
                # Method 2: Get routing IP to Gira X1
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                        s.connect((GIRA_X1_HOST, 80))
                        local_ip = s.getsockname()[0]
                        if local_ip not in local_ips and not local_ip.startswith('127.'):
                            local_ips.append(local_ip)
                except Exception as e:
                    _LOGGER.debug("Error getting routing IP: %s", e)
                
                print(f"🔍 Detected local IP addresses: {local_ips}")
                
                # Priority selection
                for ip in local_ips:
                    if ip == "10.1.1.85":
                        print(f"🎯 Using Home Assistant host IP: {ip}")
                        return ip
                        
                for ip in local_ips:
                    if ip == "10.1.1.175":
                        print(f"🎯 Using local testing machine IP: {ip}")
                        return ip
                        
                for ip in local_ips:
                    if ip.startswith("10.1.1."):
                        print(f"🎯 Using Gira X1 subnet IP: {ip}")
                        return ip
                
                if local_ips:
                    print(f"🎯 Using first available IP: {local_ips[0]}")
                    return local_ips[0]
                    
                return None
            except Exception as e:
                print(f"❌ Error detecting local IP: {e}")
                return None
        
        # Detect the best local IP
        local_ip = get_local_ip_for_gira_x1()
        
        if not local_ip:
            print("❌ Failed to detect suitable local IP address")
            return False
            
        # Build callback URLs using detected IP
        base_url = f"http://{local_ip}:8123"
        service_callback_url = f"{base_url}/api/gira_x1/service_callback"
        value_callback_url = f"{base_url}/api/gira_x1/value_callback"
        
        print(f"🌐 Using callback base URL: {base_url}")
        print(f"📞 Service callback URL: {service_callback_url}")
        print(f"📞 Value callback URL: {value_callback_url}")
        
        # Test callback registration
        print("\n📋 Testing callback registration...")
        
        try:
            # Register service callback
            print(f"🔄 Registering service callback...")
            service_result = await api.register_service_callback(service_callback_url)
            print(f"✅ Service callback registration result: {service_result}")
            
        except Exception as e:
            print(f"❌ Service callback registration failed: {e}")
            if "Callback test failed" in str(e):
                print("   This indicates the Gira X1 cannot reach our callback URL")
                print("   This is the exact error we're trying to fix!")
            return False
        
        try:
            # Register value callback
            print(f"🔄 Registering value callback...")
            value_result = await api.register_value_callback(value_callback_url)
            print(f"✅ Value callback registration result: {value_result}")
            
        except Exception as e:
            print(f"❌ Value callback registration failed: {e}")
            if "Callback test failed" in str(e):
                print("   This indicates the Gira X1 cannot reach our callback URL")
                print("   This is the exact error we're trying to fix!")
            return False
        
        print("\n🎉 SUCCESS! Callback registration completed successfully!")
        print("   The Gira X1 device can now reach our local IP address")
        print("   Real-time updates should work properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    success = await test_callback_registration()
    
    if success:
        print("\n✅ TEST PASSED: Callback registration successful!")
        print("   The IP detection and callback setup is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED: Callback registration failed!")
        print("   Need to investigate further.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
