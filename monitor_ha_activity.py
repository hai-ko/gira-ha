#!/usr/bin/env python3
"""
Home Assistant Integration Activity Monitor
==========================================

Monitor Home Assistant logs for Gira X1 coordinator activity to see if it's actually running.
This will help us understand if the coordinator is working at all.
"""

import subprocess
import re
import time
from datetime import datetime

def monitor_ha_logs():
    """Monitor Home Assistant logs for Gira X1 activity."""
    print("🔍 Monitoring Home Assistant logs for Gira X1 activity...")
    print("=" * 70)
    print("Looking for coordinator updates, polling, and state changes...")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    try:
        # Use journalctl to follow Home Assistant logs
        cmd = ["journalctl", "-u", "home-assistant@homeassistant", "-f", "--since", "1 minute ago"]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        gira_patterns = [
            r"gira.*x1",
            r"coordinator.*update",
            r"polling.*cycle",
            r"data.*update",
            r"callback",
            r"async_update_data",
            r"GiraX1",
            r"10\.1\.1\.85"
        ]
        
        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in gira_patterns]
        
        activity_count = 0
        last_activity = None
        
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
                
            # Check if line contains Gira X1 related content
            is_gira_related = any(pattern.search(line) for pattern in compiled_patterns)
            
            if is_gira_related:
                activity_count += 1
                last_activity = datetime.now()
                
                # Extract timestamp and log level
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Highlight important information
                if "update" in line.lower():
                    print(f"🔄 [{timestamp}] UPDATE: {line}")
                elif "error" in line.lower():
                    print(f"❌ [{timestamp}] ERROR: {line}")
                elif "warning" in line.lower():
                    print(f"⚠️  [{timestamp}] WARNING: {line}")
                elif "polling" in line.lower():
                    print(f"📊 [{timestamp}] POLLING: {line}")
                elif "callback" in line.lower():
                    print(f"📞 [{timestamp}] CALLBACK: {line}")
                else:
                    print(f"ℹ️  [{timestamp}] INFO: {line}")
                    
        # Check for activity timeout
        if activity_count == 0:
            print("⚠️  No Gira X1 activity detected in Home Assistant logs")
            print("This could indicate:")
            print("1. The integration is not installed or enabled")
            print("2. The integration failed to start")
            print("3. The coordinator is not actually running")
            print("4. Logging level is too high to see debug messages")
            
    except FileNotFoundError:
        print("❌ journalctl not found. Trying alternative methods...")
        try_docker_logs()
    except KeyboardInterrupt:
        print(f"\n✅ Monitoring stopped. Detected {activity_count} Gira X1 related log entries")
        if last_activity:
            elapsed = (datetime.now() - last_activity).total_seconds()
            print(f"Last activity was {elapsed:.1f} seconds ago")
    except Exception as e:
        print(f"❌ Error monitoring logs: {e}")

def try_docker_logs():
    """Try to monitor Home Assistant logs via Docker."""
    print("🐳 Trying Docker logs...")
    
    try:
        # Try common Home Assistant Docker container names
        container_names = ["homeassistant", "home-assistant", "hass"]
        
        for container in container_names:
            try:
                cmd = ["docker", "logs", "-f", "--since", "1m", container]
                subprocess.run(cmd, check=True)
                return
            except subprocess.CalledProcessError:
                continue
                
        print("❌ No Home Assistant Docker container found")
        print("Manual log check required:")
        print("1. Check your Home Assistant logs manually")
        print("2. Look for 'gira' or 'x1' related entries")
        print("3. Check if the integration is actually loaded")
        
    except FileNotFoundError:
        print("❌ Docker not available")
        manual_instructions()

def manual_instructions():
    """Provide manual instructions for checking logs."""
    print("\n📋 Manual Steps to Check Home Assistant Integration:")
    print("=" * 60)
    print("1. Open Home Assistant web interface")
    print("2. Go to Settings → System → Logs")
    print("3. Search for 'gira' or 'x1'")
    print("4. Look for coordinator update messages")
    print("5. Check if integration appears in Settings → Devices & Services")
    print("\n🔍 What to look for:")
    print("- 'Starting data update cycle'")
    print("- 'Successfully received X values from device'")
    print("- Any error messages about callbacks or polling")
    print("- Coordinator initialization messages")

if __name__ == "__main__":
    monitor_ha_logs()
