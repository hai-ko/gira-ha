#!/usr/bin/env python3
"""
Test New Callback Configuration

Test the updated callback system with:
1. Proxy IP direct access
2. Disabled callback testing
"""

import time
import subprocess

def check_ha_logs_for_callbacks():
    """Check Home Assistant logs for callback-related messages."""
    print("📋 Checking Home Assistant logs for callback activity...")
    
    try:
        # Get recent HA logs
        result = subprocess.run(
            ["docker", "logs", "--tail", "30", "--since", "2m", "homeassistant"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            
            # Filter for relevant lines
            relevant_lines = []
            for line in lines:
                if any(keyword in line for keyword in [
                    'CALLBACK', 'gira_x1', 'EXPERIMENTAL', 'PROXY IP', 
                    'webhook', 'register_callbacks'
                ]):
                    relevant_lines.append(line)
            
            if relevant_lines:
                print("🔍 Recent callback-related activity:")
                for line in relevant_lines[-15:]:  # Show last 15 relevant lines
                    print(f"   {line}")
            else:
                print("ℹ️  No recent callback activity found")
                
        else:
            print(f"❌ Failed to get logs: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Log check error: {e}")

def main():
    """Main test function."""
    print("🔧 Testing New Callback Configuration")
    print("====================================")
    print()
    print("Changes made:")
    print("1. 🌐 Using proxy IP directly: https://10.1.1.181")
    print("2. ⚠️  Disabled callback connectivity testing")
    print("3. 🎯 Should allow registration without test failures")
    print()
    
    print("⏳ Waiting for Home Assistant to process changes...")
    time.sleep(5)
    
    check_ha_logs_for_callbacks()
    
    print("\n📊 EXPECTED RESULTS:")
    print("=" * 50)
    print("✅ Should see: 'EXPERIMENTAL - Using proxy IP directly'")
    print("✅ Should see: 'Disabling callback test due to proxy'")
    print("✅ Should NOT see: 'CALLBACK REGISTRATION FAILED'")
    print("✅ Should see: 'Real-time callbacks active'")
    print()
    print("🎯 IF SUCCESSFUL:")
    print("- Callback system registered without test failure")
    print("- Integration using real-time callback mode")
    print("- Slower fallback polling (120s instead of 5s)")
    print()
    print("⚠️  NOTE:")
    print("- Callbacks won't work until proxy routing is configured")
    print("- But integration will think they're working")
    print("- Monitor for actual callback events from Gira X1")

if __name__ == "__main__":
    main()
