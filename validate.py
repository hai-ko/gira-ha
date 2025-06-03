#!/usr/bin/env python3
"""Validation script for Gira X1 Home Assistant integration."""

import json
import os
import sys
from pathlib import Path


def validate_manifest():
    """Validate the manifest.json file."""
    manifest_path = Path("custom_components/gira_x1/manifest.json")
    if not manifest_path.exists():
        print("❌ manifest.json not found")
        return False
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        required_fields = ["domain", "name", "version", "config_flow", "dependencies", "requirements"]
        for field in required_fields:
            if field not in manifest:
                print(f"❌ Missing required field '{field}' in manifest.json")
                return False
        
        print("✅ manifest.json is valid")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in manifest.json: {e}")
        return False


def validate_translations():
    """Validate translations file."""
    translations_path = Path("custom_components/gira_x1/translations/en.json")
    if not translations_path.exists():
        print("❌ translations/en.json not found")
        return False
    
    try:
        with open(translations_path, 'r') as f:
            translations = json.load(f)
        
        if "config" not in translations:
            print("❌ Missing 'config' section in translations")
            return False
        
        print("✅ translations/en.json is valid")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in translations/en.json: {e}")
        return False


def validate_python_files():
    """Validate Python syntax in all integration files."""
    python_files = [
        "custom_components/gira_x1/__init__.py",
        "custom_components/gira_x1/api.py",
        "custom_components/gira_x1/config_flow.py",
        "custom_components/gira_x1/const.py",
        "custom_components/gira_x1/light.py",
        "custom_components/gira_x1/switch.py",
        "custom_components/gira_x1/cover.py",
        "custom_components/gira_x1/sensor.py",
        "custom_components/gira_x1/binary_sensor.py",
    ]
    
    all_valid = True
    for file_path in python_files:
        if not Path(file_path).exists():
            print(f"❌ {file_path} not found")
            all_valid = False
            continue
        
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"✅ {file_path} syntax is valid")
        except SyntaxError as e:
            print(f"❌ Syntax error in {file_path}: {e}")
            all_valid = False
    
    return all_valid


def main():
    """Run all validations."""
    print("🔍 Validating Gira X1 Home Assistant integration...")
    print()
    
    validations = [
        validate_manifest(),
        validate_translations(),
        validate_python_files(),
    ]
    
    print()
    if all(validations):
        print("🎉 All validations passed! The integration looks good.")
        return 0
    else:
        print("❌ Some validations failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
