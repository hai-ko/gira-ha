#!/usr/bin/env python3
"""
Set Callback URL Override for Gira X1 Integration

This script allows you to set a callback URL override that will force
the Gira X1 integration to use a specific URL for callbacks.

Usage:
    python set_callback_override.py [URL]
    
Examples:
    python set_callback_override.py https://home.hf17-1.de
    python set_callback_override.py clear  # Remove override
"""

import sys
import requests
import json

# Home Assistant configuration
HA_URL = "http://10.1.1.242:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkNmUzYWJjNmY3Mzg0NjhhYTI1ZjVlZDYzNTk5NWE4MyIsImlhdCI6MTczMzMzMzUwMywiZXhwIjoyMDQ4NjkzNTAzfQ.vhFRgJ9k1gfpHF4hn2v_YCzeBDgfK-bKQHGZ8RL3QSY"

def set_callback_override(override_url=None):
    """Set or clear the callback URL override."""
    
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }
    
    if override_url and override_url.lower() != "clear":
        # Set the override
        service_data = {
            "domain": "gira_x1",
            "service": "set_callback_override", 
            "service_data": {
                "callback_url": override_url
            }
        }
        action = f"Setting callback URL override to: {override_url}"
    else:
        # Clear the override
        service_data = {
            "domain": "gira_x1",
            "service": "clear_callback_override",
            "service_data": {}
        }
        action = "Clearing callback URL override"
    
    print(f"🔧 {action}")
    
    try:
        response = requests.post(
            f"{HA_URL}/api/services/gira_x1/set_callback_override" if override_url and override_url.lower() != "clear" else f"{HA_URL}/api/services/gira_x1/clear_callback_override",
            headers=headers,
            json={"callback_url": override_url} if override_url and override_url.lower() != "clear" else {},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Successfully {action.lower()}")
            print("🔄 Restart Home Assistant for changes to take effect")
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("🌐 Current Gira X1 Callback URL Override Manager")
        print()
        print("Usage:")
        print("  python set_callback_override.py <URL>     # Set override")
        print("  python set_callback_override.py clear     # Clear override")
        print()
        print("Examples:")
        print("  python set_callback_override.py https://home.hf17-1.de")
        print("  python set_callback_override.py clear")
        return
    
    override_url = sys.argv[1]
    set_callback_override(override_url)

if __name__ == "__main__":
    main()
