#!/usr/bin/env python3
"""
Test HTTPS connectivity to local Home Assistant instance.
"""

import asyncio
import aiohttp
import ssl

async def test_local_https():
    """Test if we can connect to local Home Assistant via HTTPS."""
    
    local_ip = "10.1.1.175"
    port = 8123
    
    print(f"Testing HTTPS connectivity to {local_ip}:{port}")
    
    # Test with SSL verification disabled (self-signed certs)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test HTTPS connection
            async with session.get(f"https://{local_ip}:{port}", ssl=ssl_context, timeout=5) as response:
                print(f"✅ HTTPS connection successful!")
                print(f"   Status: {response.status}")
                print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
                return True
                
        except aiohttp.ClientConnectorError as e:
            print(f"❌ HTTPS connection failed: {e}")
            print(f"   This suggests HTTPS is not enabled on Home Assistant")
            
            # Try HTTP as fallback
            try:
                async with session.get(f"http://{local_ip}:{port}", timeout=5) as response:
                    print(f"✅ HTTP connection successful!")
                    print(f"   Status: {response.status}")
                    print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
                    print(f"   ⚠️  But Gira X1 requires HTTPS for callbacks!")
                    return False
            except Exception as e2:
                print(f"❌ HTTP connection also failed: {e2}")
                print(f"   Home Assistant may not be running on this IP")
                return False
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_local_https())
