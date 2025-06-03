#!/usr/bin/env python3
"""
Debug script to test Gira X1 connection and diagnose entity discovery issues.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

# Your Gira X1 configuration
GIRA_HOST = "10.1.1.85"
GIRA_PORT = 80
GIRA_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"

class GiraDebugger:
    def __init__(self, host: str, port: int, token: str):
        self.host = host
        self.port = port
        self.token = token
        self.base_url = f"http://{host}:{port}"
        
    async def test_connection(self) -> bool:
        """Test basic connection to Gira X1"""
        print(f"🔍 Testing connection to {self.base_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test basic connectivity
                url = f"{self.base_url}/api/version"
                params = {"token": self.token}
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Connection successful! Gira X1 version: {data}")
                        return True
                    else:
                        print(f"❌ Connection failed with status {response.status}")
                        text = await response.text()
                        print(f"Response: {text}")
                        return False
                        
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def test_uiconfig_endpoint(self) -> Dict[str, Any]:
        """Test the UI configuration endpoint that the integration uses"""
        print(f"\n🔍 Testing UI configuration endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v2/uiconfig"
                params = {"token": self.token}
                
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ UI config endpoint successful!")
                        print(f"📊 Response contains {len(data)} top-level items")
                        
                        # Analyze the structure
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, list):
                                    print(f"  - {key}: {len(value)} items")
                                elif isinstance(value, dict):
                                    print(f"  - {key}: {len(value)} keys")
                                else:
                                    print(f"  - {key}: {type(value).__name__}")
                        
                        return data
                    else:
                        print(f"❌ UI config failed with status {response.status}")
                        text = await response.text()
                        print(f"Response: {text}")
                        return {}
                        
        except Exception as e:
            print(f"❌ UI config error: {e}")
            return {}
    
    async def analyze_functions(self, ui_config: Dict[str, Any]) -> None:
        """Analyze functions in the UI config to see what should be discovered"""
        print(f"\n🔍 Analyzing functions for entity discovery...")
        
        # Look for functions in various possible locations
        functions = []
        
        # Check common locations where functions might be stored
        possible_locations = [
            ui_config.get('functions', []),
            ui_config.get('Functions', []),
            ui_config.get('items', []),
            ui_config.get('data', []),
        ]
        
        # Also check if ui_config itself is a list
        if isinstance(ui_config, list):
            possible_locations.append(ui_config)
        
        # Flatten and find all function-like objects
        for location in possible_locations:
            if isinstance(location, list):
                for item in location:
                    if isinstance(item, dict) and ('functionType' in item or 'type' in item):
                        functions.append(item)
        
        if not functions:
            print("❌ No functions found in UI config!")
            print("🔍 Available keys in UI config:")
            if isinstance(ui_config, dict):
                for key in ui_config.keys():
                    print(f"  - {key}")
            return
        
        print(f"✅ Found {len(functions)} functions")
        
        # Group functions by type
        function_types = {}
        channel_types = {}
        
        for func in functions:
            # Check functionType
            func_type = func.get('functionType', 'unknown')
            if func_type not in function_types:
                function_types[func_type] = 0
            function_types[func_type] += 1
            
            # Check channelType  
            chan_type = func.get('channelType', 'unknown')
            if chan_type not in channel_types:
                channel_types[chan_type] = 0
            channel_types[chan_type] += 1
        
        print(f"\n📊 Function types found:")
        for func_type, count in sorted(function_types.items()):
            print(f"  - {func_type}: {count}")
            
        print(f"\n📊 Channel types found:")
        for chan_type, count in sorted(channel_types.items()):
            print(f"  - {chan_type}: {count}")
        
        # Show some example functions
        print(f"\n🔍 Example functions (first 3):")
        for i, func in enumerate(functions[:3]):
            print(f"  Function {i+1}:")
            for key, value in func.items():
                if isinstance(value, (str, int, float, bool)):
                    print(f"    {key}: {value}")
    
    async def test_values_endpoint(self) -> None:
        """Test the values endpoint to see current device states"""
        print(f"\n🔍 Testing values endpoint...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v2/values"
                params = {"token": self.token}
                
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Values endpoint successful!")
                        print(f"📊 Found {len(data)} value entries")
                        
                        # Show some examples
                        if data:
                            print(f"🔍 Example values (first 3):")
                            for i, (key, value) in enumerate(list(data.items())[:3]):
                                print(f"  {key}: {value}")
                    else:
                        print(f"❌ Values endpoint failed with status {response.status}")
                        
        except Exception as e:
            print(f"❌ Values endpoint error: {e}")

async def main():
    print("🚀 Gira X1 Integration Diagnostic Tool")
    print("=" * 50)
    
    debugger = GiraDebugger(GIRA_HOST, GIRA_PORT, GIRA_TOKEN)
    
    # Test basic connection
    if not await debugger.test_connection():
        print("\n❌ Cannot connect to Gira X1. Please check:")
        print("  - IP address is correct (10.1.1.85)")
        print("  - Device is reachable on your network")
        print("  - Token is valid")
        return
    
    # Test UI config endpoint (this is what the integration uses for discovery)
    ui_config = await debugger.test_uiconfig_endpoint()
    if not ui_config:
        print("\n❌ Cannot fetch UI configuration. This is needed for entity discovery!")
        return
    
    # Analyze functions for entity discovery
    await debugger.analyze_functions(ui_config)
    
    # Test values endpoint
    await debugger.test_values_endpoint()
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic complete!")
    print("\nNext steps:")
    print("1. Check Home Assistant logs for any Gira X1 errors")
    print("2. If functions were found, restart Home Assistant")
    print("3. Check Developer Tools > States for 'gira_x1' entities")

if __name__ == "__main__":
    asyncio.run(main())
