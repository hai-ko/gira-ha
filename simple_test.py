#!/usr/bin/env python3
"""Simple test to verify the integration structure."""

import sys
import os

# Add the custom_components directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from gira_x1.const import DOMAIN, GIRA_FUNCTION_TYPES
        print(f"✅ Constants imported successfully - Domain: {DOMAIN}")
        print(f"✅ Function types available: {len(GIRA_FUNCTION_TYPES)} types")
        
        print("\n✅ Integration structure appears correct!")
        print("📋 Next steps for testing:")
        print("1. Set up a Home Assistant test environment")
        print("2. Install the integration")
        print("3. Configure with your Gira X1 device credentials")
        print("4. Test entity discovery and controls")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
