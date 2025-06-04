#!/usr/bin/env python3
"""Test the /rest/values endpoint specifically."""

import asyncio
import aiohttp
import json

async def test_rest_values():
    """Test the /rest/values endpoint that we found."""
    
    host = "10.1.1.85"
    port = 443
    token = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"
    
    base_url = f"https://{host}:{port}"
    auth_header = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing /rest/values endpoint on {base_url}")
    print("=" * 60)
    
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        
        # Test the /rest/values endpoint
        url = f"{base_url}/rest/values"
        
        try:
            async with session.get(url, headers=auth_header) as response:
                status = response.status
                content = await response.text()
                
                print(f"Status: {status}")
                print(f"Content length: {len(content)} characters")
                print(f"Content type: {response.headers.get('content-type', 'unknown')}")
                print()
                
                if status == 200:
                    print("First 1000 characters of response:")
                    print("-" * 40)
                    print(content[:1000])
                    print("-" * 40)
                    
                    # Try to parse as JSON
                    try:
                        data = json.loads(content)
                        print(f"\n✅ Successfully parsed as JSON")
                        print(f"Type: {type(data)}")
                        
                        if isinstance(data, dict):
                            print(f"Keys: {list(data.keys())[:10]}...")  # Show first 10 keys
                            print(f"Total keys: {len(data)}")
                            
                            # Show a few sample entries
                            print("\nSample entries:")
                            for i, (key, value) in enumerate(list(data.items())[:5]):
                                print(f"  {key}: {value}")
                                
                        elif isinstance(data, list):
                            print(f"List with {len(data)} items")
                            if data:
                                print(f"First item: {data[0]}")
                                
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse as JSON: {e}")
                        
                        # Maybe it's XML or another format
                        if content.strip().startswith('<'):
                            print("Looks like XML content")
                        else:
                            print("Unknown text format")
                else:
                    print(f"❌ Request failed with status {status}")
                    print(f"Response: {content}")
                    
        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_rest_values())
