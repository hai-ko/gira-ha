#!/usr/bin/env python3
"""
Simple token generation script for Gira X1.
This script generates a new API token without requiring Home Assistant imports.
"""

import asyncio
import aiohttp
import base64
import json

# Configuration
GIRA_X1_HOST = "10.1.1.85"
GIRA_X1_PORT = 443  # Try HTTPS first
USERNAME = "heiko"  # Update this if needed
PASSWORD = "gira"   # Update this if needed

async def generate_new_token():
    """Generate a new API token."""
    print("🔑 Generating new Gira X1 API token...")
    print(f"   Host: {GIRA_X1_HOST}:{GIRA_X1_PORT}")
    print(f"   User: {USERNAME}")
    
    # Create session with SSL verification disabled (Gira uses self-signed certs)
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        
        # Create basic auth header
        credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        
        # Client registration data
        client_data = {
            "client": "de.homeassistant.gira_x1_renewed"  # Unique client ID
        }
        
        try:
            # Try HTTPS first
            url = f"https://{GIRA_X1_HOST}:{GIRA_X1_PORT}/api/v2/clients"
            
            print(f"\n📡 Attempting token generation...")
            print(f"   URL: {url}")
            
            async with session.post(url, json=client_data, headers=headers, timeout=10) as response:
                print(f"   Status: {response.status}")
                
                if response.status == 201:  # Created
                    data = await response.json()
                    token = data.get("token")
                    
                    print(f"\n✅ SUCCESS! New token generated:")
                    print(f"🎟️  Token: {token}")
                    print(f"\n📋 To update your Home Assistant integration:")
                    print(f"1. Go to Settings > Devices & Services")
                    print(f"2. Find your Gira X1 integration")
                    print(f"3. Click Configure")
                    print(f"4. Update the token to: {token}")
                    
                    # Test the new token immediately
                    await test_new_token(session, token)
                    
                    return token
                    
                elif response.status == 401:
                    print(f"❌ Authentication failed - check username/password")
                    response_text = await response.text()
                    print(f"   Response: {response_text}")
                    
                elif response.status == 200:
                    # Might be reusing existing token
                    data = await response.json()
                    token = data.get("token")
                    print(f"ℹ️  Existing token returned: {token}")
                    await test_new_token(session, token)
                    return token
                    
                else:
                    response_text = await response.text()
                    print(f"❌ Unexpected response: {response.status}")
                    print(f"   Response: {response_text}")
                    
                    # Try HTTP as fallback
                    print(f"\n🔄 Trying HTTP fallback...")
                    url_http = f"http://{GIRA_X1_HOST}:80/api/v2/clients"
                    
                    async with session.post(url_http, json=client_data, headers=headers, timeout=10) as http_response:
                        print(f"   HTTP Status: {http_response.status}")
                        
                        if http_response.status == 201:
                            data = await http_response.json()
                            token = data.get("token")
                            print(f"✅ HTTP SUCCESS! Token: {token}")
                            await test_new_token(session, token)
                            return token
                        else:
                            http_text = await http_response.text()
                            print(f"❌ HTTP also failed: {http_text}")
                            
        except aiohttp.ClientConnectorError as e:
            print(f"❌ Connection error: {e}")
            print("💡 Check that the Gira X1 device is reachable")
            
        except asyncio.TimeoutError:
            print(f"❌ Timeout connecting to Gira X1")
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    return None

async def test_new_token(session, token):
    """Test the newly generated token."""
    print(f"\n🧪 Testing new token...")
    
    # Test with token as query parameter (Gira X1 style)
    test_url = f"https://{GIRA_X1_HOST}:{GIRA_X1_PORT}/api/v2/uiconfig?token={token}"
    
    try:
        async with session.get(test_url, timeout=10) as response:
            print(f"   Test status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                functions_count = len(data.get("functions", []))
                print(f"✅ Token test PASSED! Found {functions_count} functions")
                return True
            else:
                print(f"❌ Token test failed: {response.status}")
                response_text = await response.text()
                print(f"   Response: {response_text}")
                
    except Exception as e:
        print(f"❌ Token test error: {e}")
    
    return False

async def main():
    """Main function."""
    print("🔧 GIRA X1 TOKEN GENERATOR")
    print("=" * 40)
    print("This script will generate a new API token for your Gira X1 device.")
    print("Make sure your username and password are correct in the script.")
    print()
    
    token = await generate_new_token()
    
    if token:
        print(f"\n🎉 TOKEN GENERATION COMPLETE!")
        print(f"📝 Next steps:")
        print(f"1. Update Home Assistant integration with new token")
        print(f"2. Restart Home Assistant")
        print(f"3. Check that both polling and callbacks work")
    else:
        print(f"\n❌ TOKEN GENERATION FAILED")
        print(f"🔧 Check:")
        print(f"- Gira X1 device is accessible at {GIRA_X1_HOST}")
        print(f"- Username '{USERNAME}' and password are correct")
        print(f"- API is enabled on the device")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Token generation interrupted")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
