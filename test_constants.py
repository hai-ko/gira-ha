#!/usr/bin/env python3
"""Simple test to validate constant definitions without Home Assistant dependencies."""

import sys
import os

# Add the custom_components directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_const_file():
    """Test that const.py has the required constants defined."""
    try:
        # Import the constants file directly
        const_file_path = os.path.join('custom_components', 'gira_x1', 'const.py')
        
        # Read and execute the constants file to check it's valid Python
        with open(const_file_path, 'r') as f:
            const_content = f.read()
        
        # Create a namespace to execute the constants
        const_namespace = {}
        exec(const_content, const_namespace)
        
        # Check if the required constants are defined
        required_constants = ['WEBHOOK_VALUE_CALLBACK_PATH', 'WEBHOOK_SERVICE_CALLBACK_PATH']
        missing_constants = []
        
        for const_name in required_constants:
            if const_name not in const_namespace:
                missing_constants.append(const_name)
            else:
                print(f"✅ {const_name} = {const_namespace[const_name]}")
        
        if missing_constants:
            print(f"❌ Missing constants: {missing_constants}")
            return False
        else:
            print("✅ All required constants are defined in const.py")
            return True
            
    except Exception as e:
        print(f"❌ Error testing const.py: {e}")
        return False

def main():
    """Run the simple constant validation test."""
    print("🔍 Testing Gira X1 constant definitions...\n")
    
    if test_const_file():
        print("\n🎉 Constant validation successful!")
        print("The constants are properly defined and the integration should load correctly.")
        return 0
    else:
        print("\n💥 Constant validation failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
