#!/usr/bin/env python3
"""
Direct test of Gira X1 callback registration using the API methods.
This bypasses Home Assistant imports and tests the callback registration directly.
"""

import asyncio
import aiohttp
import socket
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

# Test configuration
GIRA_X1_HOST = "10.1.1.85"  # Your Gira X1 IP
GIRA_X1_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"  # Valid token

def get_local_ip_for_gira_x1() -> str | None:
    """Get the local IP that should be used for Gira X1 callbacks."""
    try:
        hostname = socket.gethostname()
        print(f"🔍 Current hostname: {hostname}")
        
        local_ips = []
        
        # Method 1: Get IPs from hostname
        try:
            for addr_info in socket.getaddrinfo(hostname, None):
                ip = addr_info[4][0]
                if ip not in local_ips and not ip.startswith('127.'):
                    local_ips.append(ip)
        except Exception as e:
            print(f"   Error getting IPs from hostname: {e}")
        
        # Method 2: Get routing IP to Gira X1
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect((GIRA_X1_HOST, 80))
                local_ip = s.getsockname()[0]
                if local_ip not in local_ips and not local_ip.startswith('127.'):
                    local_ips.append(local_ip)
        except Exception as e:
            print(f"   Error getting routing IP: {e}")
        
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

async def test_gira_x1_connectivity():
    """Test basic connectivity to Gira X1 device."""
    
    print("=== Testing Gira X1 Connectivity and Callback Registration ===")
    
    # Detect the best local IP
    local_ip = get_local_ip_for_gira_x1()
    
    if not local_ip:
        print("❌ Failed to detect suitable local IP address")
        return False
        
    # Build callback URLs using detected IP - MUST USE HTTPS!
    base_url = f"https://{local_ip}:8123"
    service_callback_url = f"{base_url}/api/gira_x1/service_callback"
    value_callback_url = f"{base_url}/api/gira_x1/value_callback"
    
    print(f"🌐 Using callback base URL: {base_url}")
    print(f"📞 Service callback URL: {service_callback_url}")
    print(f"📞 Value callback URL: {value_callback_url}")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test basic connectivity to Gira X1
            print(f"\n📡 Testing connectivity to Gira X1 at {GIRA_X1_HOST}...")
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Get device info - Gira X1 uses token as query parameter, not Bearer header
            async with session.get(f"https://{GIRA_X1_HOST}/api/v2/uiconfig?token={GIRA_X1_TOKEN}", ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Successfully connected to Gira X1")
                    print(f"   Found {len(data.get('uiconfig', {}).get('dataPoints', []))} data points")
                else:
                    print(f"❌ Failed to connect to Gira X1: HTTP {response.status}")
                    return False
            
            # Test callback registration for both service and value callbacks
            print(f"\n🔄 Testing callback registration...")
            
            callback_data = {
                "valueCallback": value_callback_url,
                "serviceCallback": service_callback_url,
                "testCallbacks": True
            }
            
            try:
                # Register both callbacks using the correct endpoint
                async with session.post(
                    f"https://{GIRA_X1_HOST}/api/v2/clients/{GIRA_X1_TOKEN}/callbacks",
                    headers=headers,
                    json=callback_data,
                    ssl=False
                ) as response:
                    
                    response_text = await response.text()
                    print(f"   Response status: {response.status}")
                    print(f"   Response text: {response_text}")
                    
                    if response.status == 200:
                        print(f"✅ Callback registration successful!")
                        print(f"🎉 SUCCESS! Both value and service callbacks registered!")
                        print(f"   The Gira X1 device can reach our callback URL at {base_url}")
                        print(f"   Real-time updates should work properly")
                        return True
                    else:
                        print(f"❌ Callback registration failed: {response.status}")
                        print(f"   Error: {response_text}")
                        
                        if "Callback test failed" in response_text:
                            print("   ⚠️  This indicates the Gira X1 cannot reach our callback URL")
                            print("   ⚠️  This suggests network connectivity issues")
                            print("   ⚠️  Check if the IP address is reachable from the Gira X1 device")
                        
                        return False
                        
            except Exception as e:
                print(f"❌ Exception during callback registration: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Connection test failed with error: {e}")
            return False

async def main():
    """Main test function."""
    success = await test_gira_x1_connectivity()
    
    if success:
        print("\n✅ TEST PASSED: Callback registration successful!")
        print("   The IP detection and callback setup is working correctly.")
        print("   The integration should now work with real-time updates.")
    else:
        print("\n❌ TEST FAILED: Callback registration failed!")
        print("   The Gira X1 device cannot reach our detected IP address.")
        print("   This could be due to:")
        print("   - Network routing issues")
        print("   - Firewall blocking connections")
        print("   - The IP address not being accessible from Gira X1")

if __name__ == "__main__":
    asyncio.run(main())
