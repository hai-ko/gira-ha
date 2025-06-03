#!/usr/bin/env python3
"""Comprehensive validation script for all Gira X1 integration fixes."""

import os
import sys

def validate_attribute_fixes():
    """Check that all _func_id references have been fixed."""
    print("🔍 Validating attribute fixes...")
    
    files_to_check = [
        'custom_components/gira_x1/light.py',
        'custom_components/gira_x1/cover.py',
        'custom_components/gira_x1/sensor.py',
        'custom_components/gira_x1/binary_sensor.py'
    ]
    
    issues_found = []
    fixes_validated = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            issues_found.append(f"File not found: {file_path}")
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for old _func_id references
        if '_func_id' in content:
            issues_found.append(f"Found old _func_id reference in {file_path}")
        else:
            fixes_validated.append(f"✅ {file_path}: No _func_id references")
        
        # Check for proper _function["uid"] usage
        if 'self._function["uid"]' in content:
            fixes_validated.append(f"✅ {file_path}: Proper _function['uid'] usage found")
    
    return issues_found, fixes_validated

def validate_import_fixes():
    """Check that import constants are correctly used."""
    print("🔍 Validating import fixes...")
    
    files_to_check = [
        'custom_components/gira_x1/__init__.py',
        'custom_components/gira_x1/webhook.py',
        'custom_components/gira_x1/const.py'
    ]
    
    issues_found = []
    fixes_validated = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            issues_found.append(f"File not found: {file_path}")
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for old constant names
        old_constants = ['CALLBACK_VALUE_PATH', 'CALLBACK_SERVICE_PATH']
        for old_const in old_constants:
            if old_const in content and 'WEBHOOK_' + old_const not in content:
                issues_found.append(f"Found old constant {old_const} in {file_path}")
        
        # Check for new constant names
        new_constants = ['WEBHOOK_VALUE_CALLBACK_PATH', 'WEBHOOK_SERVICE_CALLBACK_PATH']
        for new_const in new_constants:
            if new_const in content:
                fixes_validated.append(f"✅ {file_path}: Uses {new_const}")
    
    return issues_found, fixes_validated

def validate_api_improvements():
    """Check that API error handling improvements are in place."""
    print("🔍 Validating API improvements...")
    
    api_file = 'custom_components/gira_x1/api.py'
    issues_found = []
    fixes_validated = []
    
    if not os.path.exists(api_file):
        issues_found.append(f"File not found: {api_file}")
        return issues_found, fixes_validated
    
    with open(api_file, 'r') as f:
        content = f.read()
    
    # Check for improved error handling
    improvements = [
        ('content-type checking', "content_type = response.headers.get('content-type'"),
        ('500 error handling', "get value failed"),
        ('MIME type handling', "Unexpected content type"),
        ('debug logging for failed datapoints', "_LOGGER.debug(f\"Datapoint {dp_uid} not available")
    ]
    
    for improvement_name, check_string in improvements:
        if check_string in content:
            fixes_validated.append(f"✅ API: {improvement_name} implemented")
        else:
            issues_found.append(f"Missing API improvement: {improvement_name}")
    
    return issues_found, fixes_validated

def validate_https_fix():
    """Check that HTTPS callback fix is in place."""
    print("🔍 Validating HTTPS callback fix...")
    
    init_file = 'custom_components/gira_x1/__init__.py'
    issues_found = []
    fixes_validated = []
    
    if not os.path.exists(init_file):
        issues_found.append(f"File not found: {init_file}")
        return issues_found, fixes_validated
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Check for HTTPS conversion logic
    if 'external_url.startswith("http://")' in content and 'https://' in content:
        fixes_validated.append("✅ HTTPS callback conversion implemented")
    else:
        issues_found.append("HTTPS callback conversion not found")
    
    return issues_found, fixes_validated

def validate_data_points_initialization():
    """Check that _data_points initialization is properly implemented."""
    print("🔍 Validating data points initialization...")
    
    files_to_check = [
        'custom_components/gira_x1/sensor.py',
        'custom_components/gira_x1/binary_sensor.py'
    ]
    
    issues_found = []
    fixes_validated = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            issues_found.append(f"File not found: {file_path}")
            continue
            
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for proper _data_points initialization
        init_pattern = 'self._data_points = {dp["name"]: dp["uid"] for dp in function.get("dataPoints", [])}'
        if init_pattern in content:
            fixes_validated.append(f"✅ {file_path}: _data_points properly initialized")
        else:
            issues_found.append(f"Missing _data_points initialization in {file_path}")
    
    return issues_found, fixes_validated

def main():
    """Run comprehensive validation of all fixes."""
    print("🔍 Comprehensive Gira X1 Integration Validation")
    print("=" * 60)
    
    all_issues = []
    all_fixes = []
    
    # Run all validation checks
    validators = [
        validate_attribute_fixes,
        validate_import_fixes,
        validate_api_improvements,
        validate_https_fix,
        validate_data_points_initialization
    ]
    
    for validator in validators:
        issues, fixes = validator()
        all_issues.extend(issues)
        all_fixes.extend(fixes)
        print()
    
    # Summary
    print("📋 VALIDATION SUMMARY")
    print("=" * 60)
    
    if all_fixes:
        print("✅ VALIDATED FIXES:")
        for fix in all_fixes:
            print(f"   {fix}")
        print()
    
    if all_issues:
        print("❌ ISSUES FOUND:")
        for issue in all_issues:
            print(f"   {issue}")
        print()
        print("💥 Validation completed with issues!")
        return 1
    else:
        print("🎉 ALL VALIDATIONS PASSED!")
        print()
        print("📋 FIXES COMPLETED:")
        print("   • Fixed AttributeError: _func_id -> _function['uid']")
        print("   • Fixed import constants: CALLBACK_*_PATH -> WEBHOOK_*_CALLBACK_PATH")
        print("   • Added HTTPS callback URL conversion")
        print("   • Improved API error handling for content types")
        print("   • Reduced log noise for unavailable datapoints")
        print("   • Added _data_points initialization in sensor classes")
        print()
        print("🚀 The integration should now run without the reported errors!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
