#!/usr/bin/env python3
"""
Quick Override Test Script

This script applies the HTTPS proxy override and restarts Home Assistant
to test the callback system with the forced proxy configuration.
"""

import subprocess
import time
import sys

def restart_homeassistant():
    """Restart Home Assistant container."""
    try:
        print("🔄 Restarting Home Assistant...")
        result = subprocess.run(
            ["docker", "restart", "homeassistant"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Home Assistant restart initiated")
            return True
        else:
            print(f"❌ Restart failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Restart timeout")
        return False
    except Exception as e:
        print(f"❌ Restart error: {e}")
        return False

def wait_for_startup():
    """Wait for Home Assistant to start up."""
    print("⏳ Waiting for Home Assistant to start up...")
    time.sleep(15)  # Give it time to start
    print("✅ Startup wait complete")

def check_logs():
    """Check recent Home Assistant logs for callback messages."""
    try:
        print("📋 Checking recent logs for callback activity...")
        result = subprocess.run(
            ["docker", "logs", "--tail", "50", "homeassistant"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            callback_lines = [line for line in lines if 'CALLBACK' in line or 'gira_x1' in line]
            
            if callback_lines:
                print("🔍 Recent callback-related log entries:")
                for line in callback_lines[-10:]:  # Last 10 relevant lines
                    print(f"   {line}")
            else:
                print("ℹ️  No recent callback log entries found")
        else:
            print(f"❌ Log check failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Log check error: {e}")

def main():
    """Main function."""
    print("🌐 Gira X1 HTTPS Proxy Override Test")
    print("=====================================")
    print()
    print("This will:")
    print("1. Restart Home Assistant with the FORCED OVERRIDE active")
    print("2. Check logs for callback registration with https://home.hf17-1.de")
    print()
    
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    # Restart Home Assistant
    if restart_homeassistant():
        wait_for_startup()
        check_logs()
        print()
        print("🧪 Test Results:")
        print("- Check if logs show 'FORCED OVERRIDE - Using HTTPS proxy - https://home.hf17-1.de'")
        print("- Check if callback registration succeeds")
        print("- Monitor for real-time updates from Gira X1")
        print()
        print("📊 To validate the complete setup, run:")
        print("   python test_complete_https_proxy_setup.py")
    else:
        print("❌ Could not restart Home Assistant")
        sys.exit(1)

if __name__ == "__main__":
    main()
