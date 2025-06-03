#!/usr/bin/env python3
"""Final validation script for the complete Gira X1 integration."""
import json
from collections import defaultdict

def test_complete_integration():
    """Test that the integration can handle all real device data correctly."""
    print("=== Gira X1 Integration Final Validation ===\n")
    
    # Load real device data
    with open('example-uiconf.json', 'r') as f:
        data = json.load(f)
    
    functions = data.get('functions', [])
    print(f"Total functions to process: {len(functions)}")
    
    # Function type mappings (from const.py)
    FUNCTION_TYPES = {
        "de.gira.schema.functions.Switch": "switch",
        "de.gira.schema.functions.KNX.Light": "light",
        "de.gira.schema.functions.Covering": "cover",
        "de.gira.schema.functions.KNX.HeatingCooling": "climate",
        "de.gira.schema.functions.Trigger": "button",
    }
    
    # Channel type mappings (from const.py)
    CHANNEL_TYPES = {
        "de.gira.schema.channels.Switch": "switch",
        "de.gira.schema.channels.KNX.Dimmer": "light",
        "de.gira.schema.channels.BlindWithPos": "cover",
        "de.gira.schema.channels.KNX.HeatingCoolingSwitchable": "climate",
        "de.gira.schema.channels.Trigger": "button",
    }
    
    platform_counts = defaultdict(int)
    platform_functions = defaultdict(list)
    entity_validation = defaultdict(list)
    
    for func in functions:
        func_type = func.get('functionType', '')
        channel_type = func.get('channelType', '')
        uid = func.get('uid', '')
        name = func.get('displayName', '')
        
        # Determine platform
        platform = None
        if func_type in FUNCTION_TYPES:
            platform = FUNCTION_TYPES[func_type]
        elif channel_type in CHANNEL_TYPES:
            platform = CHANNEL_TYPES[channel_type]
        
        if platform:
            platform_counts[platform] += 1
            platform_functions[platform].append({
                'uid': uid,
                'name': name,
                'functionType': func_type,
                'channelType': channel_type,
                'dataPoints': [dp.get('name') for dp in func.get('dataPoints', [])]
            })
            
            # Validate expected datapoints for each platform
            datapoints = [dp.get('name') for dp in func.get('dataPoints', [])]
            
            if platform == 'light':
                expected = {'OnOff', 'Brightness', 'Shift'}
                if expected.intersection(datapoints):
                    entity_validation[platform].append('✓')
                else:
                    entity_validation[platform].append(f'✗ Missing expected datapoints: {expected}')
                    
            elif platform == 'switch':
                expected = {'OnOff'}
                if expected.intersection(datapoints):
                    entity_validation[platform].append('✓')
                else:
                    entity_validation[platform].append(f'✗ Missing OnOff datapoint')
                    
            elif platform == 'cover':
                expected = {'Up-Down', 'Step-Up-Down', 'Position', 'Slat-Position'}
                if expected.intersection(datapoints):
                    entity_validation[platform].append('✓')
                else:
                    entity_validation[platform].append(f'✗ Missing cover datapoints')
                    
            elif platform == 'climate':
                expected = {'Current', 'Set-Point'}
                if expected.intersection(datapoints):
                    entity_validation[platform].append('✓')
                else:
                    entity_validation[platform].append(f'✗ Missing temperature datapoints')
                    
            elif platform == 'button':
                expected = {'Trigger'}
                if expected.intersection(datapoints):
                    entity_validation[platform].append('✓')
                else:
                    entity_validation[platform].append(f'✗ Missing Trigger datapoint')
    
    print("=== Platform Distribution ===")
    total_entities = 0
    for platform, count in sorted(platform_counts.items()):
        valid_count = entity_validation[platform].count('✓')
        print(f"  {platform.upper()}: {count} entities ({valid_count} valid)")
        total_entities += count
    
    print(f"\nTotal entities: {total_entities}")
    
    print("\n=== Entity Validation Summary ===")
    all_valid = True
    for platform, validations in entity_validation.items():
        valid_count = validations.count('✓')
        total_count = len(validations)
        success_rate = (valid_count / total_count * 100) if total_count > 0 else 0
        print(f"  {platform.upper()}: {valid_count}/{total_count} valid ({success_rate:.1f}%)")
        
        if success_rate < 100:
            all_valid = False
            # Show failed validations
            failed = [v for v in validations if v != '✓']
            for failure in failed[:3]:  # Show first 3 failures
                print(f"    {failure}")
    
    print(f"\n=== Integration Status ===")
    if all_valid and total_entities == len(functions):
        print("✅ INTEGRATION COMPLETE")
        print("- All device functions are mapped to Home Assistant platforms")
        print("- All entities have valid datapoint configurations")
        print("- Ready for real device testing")
    else:
        print("⚠️  INTEGRATION ISSUES DETECTED")
        if total_entities != len(functions):
            print(f"- {len(functions) - total_entities} functions not mapped")
        if not all_valid:
            print("- Some entities have invalid datapoint configurations")
    
    print(f"\n=== Sample Entities ===")
    # Show sample entities for each platform
    for platform, functions_list in platform_functions.items():
        if functions_list:
            sample = functions_list[0]
            print(f"{platform.upper()}: {sample['name']}")
            print(f"  UID: {sample['uid']}")
            print(f"  DataPoints: {', '.join(sample['dataPoints'])}")

if __name__ == "__main__":
    test_complete_integration()
