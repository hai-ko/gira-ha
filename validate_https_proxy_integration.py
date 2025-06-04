#!/usr/bin/env python3
"""
Simple test to verify HTTPS proxy configuration in integration code.

This test checks that the integration code has been updated to use the HTTPS proxy
for callback URLs instead of the local IP that was causing SSL issues.
"""

import re


def test_https_proxy_in_code():
    """Test that HTTPS proxy URL is configured in the integration."""
    print("🔍 Checking integration code for HTTPS proxy configuration...")
    
    try:
        with open('/Users/heikoburkhardt/repos/gira-x1-ha/custom_components/gira_x1/__init__.py', 'r') as f:
            code = f.read()
        
        # Check for HTTPS proxy URL
        if 'https://home.hf17-1.de' in code:
            print("   ✅ HTTPS proxy URL found in integration code")
            
            # Check context around the proxy URL
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if 'https://home.hf17-1.de' in line:
                    print(f"   Found at line {i+1}: {line.strip()}")
                    
                    # Show surrounding context
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    print("   Context:")
                    for j in range(start, end):
                        marker = ">>>" if j == i else "   "
                        print(f"   {marker} {j+1}: {lines[j]}")
                    
                    return True
            
        else:
            print("   ❌ HTTPS proxy URL not found in integration code")
            print("   Looking for any HTTPS URLs...")
            
            https_urls = re.findall(r'https://[^\s"\']+', code)
            if https_urls:
                print(f"   Found HTTPS URLs: {https_urls}")
            else:
                print("   No HTTPS URLs found")
            
            return False
            
    except Exception as e:
        print(f"   ❌ Error reading integration code: {e}")
        return False


def test_callback_url_logic():
    """Test the callback URL generation logic."""
    print("\n🔗 Checking callback URL generation logic...")
    
    try:
        with open('/Users/heikoburkhardt/repos/gira-x1-ha/custom_components/gira_x1/__init__.py', 'r') as f:
            code = f.read()
        
        # Check for callback URL generation function
        if '_get_callback_base_url' in code:
            print("   ✅ Callback URL generation method found")
            
            # Extract the method
            method_start = code.find('def _get_callback_base_url')
            if method_start > 0:
                # Find the end of the method (next method or class)
                method_end = code.find('\n    def ', method_start + 1)
                if method_end == -1:
                    method_end = code.find('\n\nclass ', method_start + 1)
                if method_end == -1:
                    method_end = len(code)
                
                method_code = code[method_start:method_end]
                
                # Check for key features
                checks = {
                    'HTTPS proxy': 'https://home.hf17-1.de' in method_code,
                    'SSL logging': 'SSL/TLS' in method_code,
                    'Proxy logging': 'HTTPS PROXY' in method_code,
                    'Fallback logic': 'external_url' in method_code,
                }
                
                print("   Method analysis:")
                for check_name, passed in checks.items():
                    status = "✅" if passed else "❌"
                    print(f"     {status} {check_name}")
                
                return all(checks.values())
            else:
                print("   ❌ Could not extract method code")
                return False
        else:
            print("   ❌ Callback URL generation method not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error analyzing callback logic: {e}")
        return False


def test_logging_messages():
    """Test that proper logging messages are in place."""
    print("\n📝 Checking logging messages...")
    
    try:
        with open('/Users/heikoburkhardt/repos/gira-x1-ha/custom_components/gira_x1/__init__.py', 'r') as f:
            code = f.read()
        
        expected_logs = [
            'CALLBACK URL: Using HTTPS proxy',
            'HTTPS PROXY: This should resolve SSL/TLS connectivity issues',
            'IP DETECTION:',
        ]
        
        found_logs = []
        for log_msg in expected_logs:
            if log_msg in code:
                found_logs.append(log_msg)
                print(f"   ✅ Found: '{log_msg}'")
            else:
                print(f"   ❌ Missing: '{log_msg}'")
        
        return len(found_logs) == len(expected_logs)
        
    except Exception as e:
        print(f"   ❌ Error checking logging: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🧪 HTTPS PROXY INTEGRATION VALIDATION")
    print("=" * 45)
    
    # Test 1: Check for HTTPS proxy in code
    proxy_test = test_https_proxy_in_code()
    
    # Test 2: Check callback URL logic
    logic_test = test_callback_url_logic()
    
    # Test 3: Check logging messages
    logging_test = test_logging_messages()
    
    print(f"\n📊 VALIDATION RESULTS:")
    print(f"HTTPS Proxy in Code:    {'✅ PASS' if proxy_test else '❌ FAIL'}")
    print(f"Callback URL Logic:     {'✅ PASS' if logic_test else '❌ FAIL'}")
    print(f"Logging Messages:       {'✅ PASS' if logging_test else '❌ FAIL'}")
    
    if proxy_test and logic_test and logging_test:
        print(f"\n🎉 SUCCESS!")
        print(f"   Integration has been updated to use HTTPS proxy")
        print(f"   URL: https://home.hf17-1.de")
        print(f"   This should resolve the SSL/TLS connectivity issues")
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Restart Home Assistant")
        print(f"   2. Check Home Assistant logs for proxy usage")
        print(f"   3. Test Gira X1 callback registration")
    else:
        print(f"\n❌ ISSUES FOUND:")
        print(f"   Integration may not be properly configured for HTTPS proxy")
        
    return proxy_test and logic_test and logging_test


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
