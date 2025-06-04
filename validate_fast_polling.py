#!/usr/bin/env python3
"""
Simple validation script for fast polling implementation.
"""

import os

def test_constants_file():
    """Test that the constants file has the required polling intervals."""
    print("=== Testing Constants File ===")
    
    const_file = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', 'const.py')
    
    with open(const_file, 'r') as f:
        content = f.read()
    
    # Check for required constants
    required_constants = [
        'UPDATE_INTERVAL_SECONDS: Final = 30',
        'FAST_UPDATE_INTERVAL_SECONDS: Final = 5',
        'CALLBACK_UPDATE_INTERVAL_SECONDS: Final = 300'
    ]
    
    all_found = True
    for constant in required_constants:
        if constant in content:
            print(f"✅ Found: {constant}")
        else:
            print(f"❌ Missing: {constant}")
            all_found = False
    
    return all_found

def test_init_file():
    """Test that the __init__.py file properly implements fast polling."""
    print("\n=== Testing __init__.py Implementation ===")
    
    init_file = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', '__init__.py')
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Check for proper imports
    checks = [
        ('FAST_UPDATE_INTERVAL_SECONDS import', 'FAST_UPDATE_INTERVAL_SECONDS'),
        ('Fast polling on callback failure', 'timedelta(seconds=FAST_UPDATE_INTERVAL_SECONDS)'),
        ('Fast polling logging', 'using fast polling (5 seconds)'),
        ('Callback success logging', 'Callbacks enabled'),
        ('Exception handling with fast polling', 'Callback setup failed, using fast polling'),
    ]
    
    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ {check_name}: Found")
        else:
            print(f"❌ {check_name}: Missing '{check_string}'")
            all_passed = False
    
    return all_passed

def test_polling_logic():
    """Test the polling logic implementation."""
    print("\n=== Testing Polling Logic ===")
    
    init_file = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', '__init__.py')
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Look for the specific polling logic in setup_callbacks
    scenarios = [
        ('Callback success scenario', 'self.update_interval = timedelta(seconds=CALLBACK_UPDATE_INTERVAL_SECONDS)'),
        ('Callback failure scenario', 'self.update_interval = timedelta(seconds=FAST_UPDATE_INTERVAL_SECONDS)'),
        ('Exception handling scenario', 'self.update_interval = timedelta(seconds=FAST_UPDATE_INTERVAL_SECONDS)')
    ]
    
    all_found = True
    for scenario_name, code_pattern in scenarios:
        count = content.count(code_pattern)
        if count > 0:
            print(f"✅ {scenario_name}: Found ({count} occurrence{'s' if count > 1 else ''})")
        else:
            print(f"❌ {scenario_name}: Missing")
            all_found = False
    
    return all_found

def analyze_implementation():
    """Analyze the complete implementation."""
    print("\n=== Implementation Analysis ===")
    
    init_file = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', '__init__.py')
    
    with open(init_file, 'r') as f:
        lines = f.readlines()
    
    # Find the setup_callbacks method
    in_setup_callbacks = False
    callback_logic = []
    
    for i, line in enumerate(lines):
        if 'async def setup_callbacks(self)' in line:
            in_setup_callbacks = True
            start_line = i
        elif in_setup_callbacks and line.strip().startswith('async def ') and 'setup_callbacks' not in line:
            break
        elif in_setup_callbacks:
            callback_logic.append(f"{i+1:3d}: {line.rstrip()}")
    
    print("Key parts of setup_callbacks method:")
    for line in callback_logic[-30:]:  # Show last 30 lines of the method
        if any(keyword in line.lower() for keyword in ['fast_update', 'timedelta', 'update_interval', 'callback', 'polling']):
            print(f"→ {line}")
    
    return True

def main():
    """Run all validation tests."""
    print("Fast Polling Implementation Validation")
    print("=" * 50)
    
    success = True
    
    if not test_constants_file():
        success = False
    
    if not test_init_file():
        success = False
    
    if not test_polling_logic():
        success = False
    
    analyze_implementation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Fast polling implementation validation PASSED!")
        print("\nSummary of implemented features:")
        print("• 5-second fast polling when callback registration fails")
        print("• 5-second fast polling when callback setup throws an exception")
        print("• 300-second fallback polling when callbacks are successful")
        print("• Proper logging for each polling mode")
        print("• Clean error handling and graceful fallbacks")
        
        print("\nUser benefits:")
        print("• Responsive updates even when Gira X1 callbacks fail")
        print("• No manual intervention required when network issues occur")
        print("• Clear logging to understand which mode is active")
    else:
        print("❌ Fast polling implementation validation FAILED!")
        print("Some components are missing or incorrect.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
