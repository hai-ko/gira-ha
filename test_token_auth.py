#!/usr/bin/env python3
"""Test script for Gira X1 token authentication."""
import asyncio
import sys
import json
from pathlib import Path

# Add the custom component to the path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

from gira_x1.api import GiraX1Client, GiraX1AuthError, GiraX1ConnectionError


class MockHass:
    """Mock Home Assistant for testing."""
    pass


async def test_token_auth():
    """Test token authentication."""
    print("=== Gira X1 Token Authentication Test ===\n")
    
    # Configuration
    host = input("Enter Gira X1 host IP: ").strip()
    port = int(input("Enter port (default 80): ").strip() or "80")
    
    auth_method = input("Choose auth method (1=password, 2=token): ").strip()
    
    if auth_method == "1":
        username = input("Enter username: ").strip()
        password = input("Enter password: ").strip()
        
        print(f"\n🔐 Testing username/password authentication...")
        client = GiraX1Client(MockHass(), host, port, username=username, password=password)
    else:
        token = input("Enter API token: ").strip()
        
        print(f"\n🎟️  Testing token authentication...")
        client = GiraX1Client(MockHass(), host, port, token=token)
    
    try:
        # Test authentication
        print("Authenticating...")
        if await client.register_client():
            print("✅ Authentication successful!")
            
            # Test API call
            print("Testing API call...")
            uiconfig = await client.get_uiconfig()
            
            if uiconfig:
                functions_count = len(uiconfig.get("functions", []))
                print(f"✅ API call successful! Found {functions_count} functions.")
                
                # Show some sample functions
                functions = uiconfig.get("functions", [])[:3]
                print("\n📋 Sample functions:")
                for i, func in enumerate(functions):
                    print(f"  {i+1}. {func.get('displayName', 'Unknown')} ({func.get('functionType', 'Unknown type')})")
                
            else:
                print("⚠️  API call returned empty data")
                
            print(f"\n🔑 Active token: {client._token}")
            
        else:
            print("❌ Authentication failed!")
            
    except GiraX1AuthError as e:
        print(f"❌ Authentication error: {e}")
    except GiraX1ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        print("\nCleaning up...")
        await client.logout()
        print("✅ Cleanup complete!")


async def test_token_generation():
    """Test generating a new token using credentials."""
    print("=== Token Generation Test ===\n")
    
    host = input("Enter Gira X1 host IP: ").strip()
    port = int(input("Enter port (default 80): ").strip() or "80")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    
    print(f"\n🔧 Generating token for {username}@{host}:{port}...")
    
    client = GiraX1Client(MockHass(), host, port, username=username, password=password)
    
    try:
        if await client.register_client():
            token = client._token
            print(f"✅ Token generated successfully!")
            print(f"🎟️  Your API token: {token}")
            print(f"\n📝 You can now use this token in your configuration:")
            print(f"    auth_method: token")
            print(f"    token: {token}")
            
            # Don't logout so the token remains valid
            print("\n⚠️  Token will remain active (not revoked)")
            
        else:
            print("❌ Token generation failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Main test function."""
    print("Gira X1 Authentication Test Tool\n")
    print("Choose test mode:")
    print("1. Test existing authentication (username/password or token)")
    print("2. Generate new API token")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        await test_token_auth()
    elif choice == "2":
        await test_token_generation()
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
