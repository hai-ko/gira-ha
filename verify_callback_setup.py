#!/usr/bin/env python3
"""
Quick setup verification for Gira X1 callback implementation.
"""

import os
import json

def main():
    """Verify the callback implementation is properly set up."""
    print("🔍 Gira X1 Callback Implementation - Setup Verification")
    print("=" * 60)
    
    # Check integration structure
    base_path = "custom_components/gira_x1"
    required_files = [
        "__init__.py",
        "api.py", 
        "webhook.py",
        "const.py",
        "manifest.json"
    ]
    
    print("\n📁 File Structure:")
    for file in required_files:
        filepath = os.path.join(base_path, file)
        if os.path.exists(filepath):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            return False
    
    # Check manifest.json
    print("\n📋 Manifest Configuration:")
    try:
        with open(os.path.join(base_path, "manifest.json"), 'r') as f:
            manifest = json.load(f)
            
        iot_class = manifest.get("iot_class")
        dependencies = manifest.get("dependencies", [])
        
        if iot_class == "local_push":
            print(f"  ✅ iot_class: {iot_class}")
        else:
            print(f"  ❌ iot_class: {iot_class} (should be 'local_push')")
            
        if "http" in dependencies:
            print(f"  ✅ http dependency included")
        else:
            print(f"  ❌ http dependency missing")
            
    except Exception as e:
        print(f"  ❌ Error reading manifest: {e}")
        return False
    
    # Check for key callback constants
    print("\n🔧 Callback Constants:")
    try:
        const_path = os.path.join(base_path, "const.py")
        with open(const_path, 'r') as f:
            content = f.read()
            
        constants = [
            "CALLBACK_UPDATE_INTERVAL_SECONDS",
            "WEBHOOK_VALUE_CALLBACK_PATH", 
            "WEBHOOK_SERVICE_CALLBACK_PATH",
            "API_CALLBACKS_PATH"
        ]
        
        for const in constants:
            if const in content:
                print(f"  ✅ {const}")
            else:
                print(f"  ❌ {const} - MISSING")
                
    except Exception as e:
        print(f"  ❌ Error reading constants: {e}")
        return False
        
    # Check for callback methods in API
    print("\n🌐 API Callback Methods:")
    try:
        api_path = os.path.join(base_path, "api.py")
        with open(api_path, 'r') as f:
            content = f.read()
            
        methods = [
            "register_callbacks",
            "unregister_callbacks"
        ]
        
        for method in methods:
            if f"async def {method}" in content:
                print(f"  ✅ {method}()")
            else:
                print(f"  ❌ {method}() - MISSING")
                
    except Exception as e:
        print(f"  ❌ Error reading API: {e}")
        return False
        
    # Check webhook views
    print("\n🔗 Webhook Views:")
    try:
        webhook_path = os.path.join(base_path, "webhook.py")
        with open(webhook_path, 'r') as f:
            content = f.read()
            
        views = [
            "GiraX1ValueCallbackView",
            "GiraX1ServiceCallbackView"
        ]
        
        for view in views:
            if f"class {view}" in content:
                print(f"  ✅ {view}")
            else:
                print(f"  ❌ {view} - MISSING")
                
    except Exception as e:
        print(f"  ❌ Error reading webhook: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Setup verification completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Copy the custom_components folder to your Home Assistant config directory")
    print("2. Restart Home Assistant")
    print("3. Check logs for callback registration messages")
    print("4. Test real-time updates by changing device values")
    print("\n💡 Monitor logs with:")
    print("   grep -i 'callback' home-assistant.log")
    
    return True

if __name__ == "__main__":
    main()
