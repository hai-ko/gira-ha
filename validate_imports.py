#!/usr/bin/env python3
"""Validate that the import fixes are correctly implemented."""

import sys
import os

# Add the custom_components directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def validate_const_imports():
    """Test that constants can be imported from const.py."""
    try:
        from gira_x1.const import WEBHOOK_VALUE_CALLBACK_PATH, WEBHOOK_SERVICE_CALLBACK_PATH
        print("✅ Constants imported successfully from const.py:")
        print(f"  WEBHOOK_VALUE_CALLBACK_PATH = {WEBHOOK_VALUE_CALLBACK_PATH}")
        print(f"  WEBHOOK_SERVICE_CALLBACK_PATH = {WEBHOOK_SERVICE_CALLBACK_PATH}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import constants from const.py: {e}")
        return False

def validate_init_imports():
    """Test that __init__.py can import the constants."""
    try:
        # Read the __init__.py file and check if it has the correct imports
        init_file = os.path.join('custom_components', 'gira_x1', '__init__.py')
        with open(init_file, 'r') as f:
            content = f.read()
        
        # Check if the correct constants are imported
        if 'WEBHOOK_VALUE_CALLBACK_PATH' in content and 'WEBHOOK_SERVICE_CALLBACK_PATH' in content:
            print("✅ __init__.py contains correct constant imports")
            return True
        else:
            print("❌ __init__.py does not contain the expected constant imports")
            return False
    except Exception as e:
        print(f"❌ Error checking __init__.py: {e}")
        return False

def validate_webhook_imports():
    """Test that webhook.py can import the constants."""
    try:
        # Read the webhook.py file and check if it has the correct imports
        webhook_file = os.path.join('custom_components', 'gira_x1', 'webhook.py')
        with open(webhook_file, 'r') as f:
            content = f.read()
        
        # Check if the correct constants are imported and used
        if ('WEBHOOK_VALUE_CALLBACK_PATH' in content and 
            'WEBHOOK_SERVICE_CALLBACK_PATH' in content and
            'url = WEBHOOK_VALUE_CALLBACK_PATH' in content and
            'url = WEBHOOK_SERVICE_CALLBACK_PATH' in content):
            print("✅ webhook.py contains correct constant imports and usage")
            return True
        else:
            print("❌ webhook.py does not contain the expected constant imports or usage")
            return False
    except Exception as e:
        print(f"❌ Error checking webhook.py: {e}")
        return False

def validate_no_old_constants():
    """Ensure the old incorrect constant names are not being used."""
    files_to_check = [
        os.path.join('custom_components', 'gira_x1', '__init__.py'),
        os.path.join('custom_components', 'gira_x1', 'webhook.py')
    ]
    
    old_constants = ['CALLBACK_VALUE_PATH', 'CALLBACK_SERVICE_PATH']
    all_clean = True
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            for old_const in old_constants:
                if old_const in content:
                    print(f"❌ Found old constant '{old_const}' in {file_path}")
                    all_clean = False
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            all_clean = False
    
    if all_clean:
        print("✅ No old incorrect constant names found")
    
    return all_clean

def main():
    """Run all validation tests."""
    print("🔍 Validating Gira X1 integration import fixes...\n")
    
    tests = [
        validate_const_imports,
        validate_init_imports,
        validate_webhook_imports,
        validate_no_old_constants
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()  # Add spacing between tests
    
    if all_passed:
        print("🎉 All validation tests passed!")
        print("The import errors should be resolved and the integration should load correctly.")
        return 0
    else:
        print("💥 Some validation tests failed!")
        print("There may still be import issues that need to be addressed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
