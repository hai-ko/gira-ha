#!/usr/bin/env python3
"""
Simple test to check basic Gira X1 API availability and token validity.
"""

import asyncio
import aiohttp

GIRA_X1_HOST = "10.1.1.85"
GIRA_X1_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"

async def test_basic_api():
    """Test basic API availability and token validity."""
    
    print("=== Basic Gira X1 API Test ===")
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Check API availability (no auth required)
        print(f"📡 Testing API availability at {GIRA_X1_HOST}...")
        try:
            # Try HTTPS first (as per Gira documentation)
            async with session.get(f"https://{GIRA_X1_HOST}/api/v2/", ssl=False) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    try:
                        data = await response.json()
                        print(f"✅ API is available!")
                        print(f"   Device: {data.get('deviceName', 'Unknown')}")
                        print(f"   Type: {data.get('deviceType', 'Unknown')}")
                        print(f"   Version: {data.get('deviceVersion', 'Unknown')}")
                    except Exception as e:
                        text = await response.text()
                        print(f"   Raw response: {text[:200]}...")
                else:
                    text = await response.text()
                    print(f"❌ API not available: {text[:200]}...")
                    return False
        except Exception as e:
            print(f"❌ Failed to connect to API: {e}")
            return False
        
        # Test 2: Test token validity with uiconfig endpoint
        print(f"\n🔑 Testing token validity...")
        try:
            async with session.get(f"https://{GIRA_X1_HOST}/api/v2/uiconfig?token={GIRA_X1_TOKEN}", ssl=False) as response:
                print(f"   Status: {response.status}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'application/json' in content_type:
                        try:
                            data = await response.json()
                            functions_count = len(data.get('uiconfig', {}).get('functions', []))
                            datapoints_count = len(data.get('uiconfig', {}).get('dataPoints', []))
                            print(f"✅ Token is valid!")
                            print(f"   Found {functions_count} functions")
                            print(f"   Found {datapoints_count} data points")
                            return True
                        except Exception as e:
                            print(f"❌ Failed to parse JSON response: {e}")
                            text = await response.text()
                            print(f"   Raw response: {text[:200]}...")
                            return False
                    else:
                        print(f"❌ Unexpected content type: {content_type}")
                        text = await response.text()
                        print(f"   Raw response: {text[:200]}...")
                        if "login" in text.lower() or "authentication" in text.lower():
                            print("   ⚠️  Appears to be a login page - token might be invalid")
                        return False
                elif response.status == 401:
                    print(f"❌ Token authentication failed (401 Unauthorized)")
                    return False
                else:
                    text = await response.text()
                    print(f"❌ Unexpected response: {response.status}")
                    print(f"   Raw response: {text[:200]}...")
                    return False
                    
        except Exception as e:
            print(f"❌ Failed to test token: {e}")
            return False

async def main():
    """Main test function."""
    success = await test_basic_api()
    
    if success:
        print(f"\n✅ SUCCESS: API is available and token is valid!")
        print(f"   Ready to test callback registration")
    else:
        print(f"\n❌ FAILED: API or token issues detected")
        print(f"   Please check:")
        print(f"   - Gira X1 device is reachable at {GIRA_X1_HOST}")
        print(f"   - Token '{GIRA_X1_TOKEN}' is valid")
        print(f"   - API is enabled on the device")

if __name__ == "__main__":
    asyncio.run(main())
