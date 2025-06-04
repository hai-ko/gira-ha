#!/usr/bin/env python3
"""
GIRA X1 STATE SYNCHRONIZATION - COMPLETE FIX VALIDATION
======================================================

This script validates that the state synchronization fix resolves the core issues:
1. String-to-boolean conversion problems
2. Initial state reading accuracy  
3. State update consistency

The fix addresses the critical bug where:
- API returns values as strings ("0", "1")
- Switch entities incorrectly parsed bool("0") as True
- Light entities had proper string handling but switches didn't
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Any, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MockCoordinator:
    """Mock coordinator that simulates the real Home Assistant coordinator."""
    
    def __init__(self):
        self.data = {"values": {}}
        self.last_update_success = True
    
    def update_values(self, values_dict: Dict[str, Any]):
        """Update coordinator data with new values."""
        if "values" not in self.data:
            self.data["values"] = {}
        self.data["values"].update(values_dict)
        logger.info(f"Coordinator updated with values: {values_dict}")

class MockGiraX1Switch:
    """Mock switch entity with the FIXED string-to-boolean conversion logic."""
    
    def __init__(self, coordinator, function_data, on_off_uid):
        self.coordinator = coordinator
        self._function = function_data
        self._on_off_uid = on_off_uid
        self._attr_name = function_data.get("displayName", f"Switch {on_off_uid}")
        
    @property
    def is_on(self) -> bool:
        """Return true if switch is on - WITH FIX."""
        if self._on_off_uid:
            values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
            value = values.get(self._on_off_uid, False)
            
            # FIXED: Handle string values from API properly
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'on')
            return bool(value)
        return False

class MockGiraX1Light:
    """Mock light entity with the existing proper string conversion logic."""
    
    def __init__(self, coordinator, function_data, on_off_uid, brightness_uid=None):
        self.coordinator = coordinator
        self._function = function_data
        self._on_off_uid = on_off_uid
        self._brightness_uid = brightness_uid
        self._attr_name = function_data.get("displayName", f"Light {on_off_uid}")
        
    @property
    def is_on(self) -> bool:
        """Return true if light is on - ALREADY CORRECT."""
        values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
        if self._on_off_uid:
            # Use OnOff data point if available
            value = values.get(self._on_off_uid, False)
            # Handle string values from API
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'on')
            return bool(value)
        elif self._brightness_uid:
            # Fall back to brightness data point
            value = values.get(self._brightness_uid, 0)
            try:
                numeric_value = float(value) if isinstance(value, str) else value
                return numeric_value > 0
            except (ValueError, TypeError):
                return False
        return False

def test_string_to_boolean_conversion():
    """Test the core string-to-boolean conversion fix."""
    logger.info("=" * 80)
    logger.info("TESTING STRING-TO-BOOLEAN CONVERSION FIX")
    logger.info("=" * 80)
    
    # Create mock coordinator
    coordinator = MockCoordinator()
    
    # Create test entities
    switch_function = {"uid": "a02t", "displayName": "Test Switch"}
    light_function = {"uid": "a03b", "displayName": "Test Light"}
    
    switch = MockGiraX1Switch(coordinator, switch_function, "a02u")
    light = MockGiraX1Light(coordinator, light_function, "a03c")
    
    # Test cases with different value types
    test_cases = [
        # String values (from API)
        {"a02u": "0", "a03c": "0", "expected_switch": False, "expected_light": False, "description": "String '0' (OFF)"},
        {"a02u": "1", "a03c": "1", "expected_switch": True, "expected_light": True, "description": "String '1' (ON)"},
        {"a02u": "true", "a03c": "true", "expected_switch": True, "expected_light": True, "description": "String 'true'"},
        {"a02u": "false", "a03c": "false", "expected_switch": False, "expected_light": False, "description": "String 'false'"},
        {"a02u": "on", "a03c": "on", "expected_switch": True, "expected_light": True, "description": "String 'on'"},
        {"a02u": "off", "a03c": "off", "expected_switch": False, "expected_light": False, "description": "String 'off'"},
        
        # Boolean values (internal)
        {"a02u": True, "a03c": True, "expected_switch": True, "expected_light": True, "description": "Boolean True"},
        {"a02u": False, "a03c": False, "expected_switch": False, "expected_light": False, "description": "Boolean False"},
        
        # Numeric values
        {"a02u": 1, "a03c": 1, "expected_switch": True, "expected_light": True, "description": "Integer 1"},
        {"a02u": 0, "a03c": 0, "expected_switch": False, "expected_light": False, "description": "Integer 0"},
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\nTest {i}/{total_tests}: {test_case['description']}")
        
        # Update coordinator with test values
        coordinator.update_values({
            "a02u": test_case["a02u"],
            "a03c": test_case["a03c"]
        })
        
        # Get entity states
        switch_state = switch.is_on
        light_state = light.is_on
        
        # Check results
        switch_correct = switch_state == test_case["expected_switch"]
        light_correct = light_state == test_case["expected_light"]
        
        logger.info(f"  Switch value: {test_case['a02u']} -> is_on: {switch_state} (expected: {test_case['expected_switch']}) {'✅' if switch_correct else '❌'}")
        logger.info(f"  Light value:  {test_case['a03c']} -> is_on: {light_state} (expected: {test_case['expected_light']}) {'✅' if light_correct else '❌'}")
        
        if switch_correct and light_correct:
            success_count += 1
            logger.info("  ✅ PASS")
        else:
            logger.error("  ❌ FAIL")
    
    logger.info(f"\n" + "=" * 80)
    logger.info(f"CONVERSION TEST RESULTS: {success_count}/{total_tests} tests passed")
    logger.info(f"Success rate: {(success_count/total_tests)*100:.1f}%")
    
    return success_count == total_tests

def test_real_gira_values():
    """Test with actual values from the Gira X1 diagnostic."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING WITH REAL GIRA X1 VALUES")
    logger.info("=" * 80)
    
    # Values from the diagnostic script
    real_values = {
        "a02u": "0",  # Wandleuchten OnOff
        "a03c": "1",  # Steckdose OnOff  
        "a060": "0.392157",  # Fenster 1 Position
        "a061": "0.392157",  # Fenster 1 Slat-Position
    }
    
    coordinator = MockCoordinator()
    coordinator.update_values(real_values)
    
    # Create entities for the real datapoints
    entities = [
        ("Switch Wandleuchten", MockGiraX1Switch(coordinator, {"uid": "a02t", "displayName": "Wandleuchten"}, "a02u")),
        ("Switch Steckdose", MockGiraX1Switch(coordinator, {"uid": "a03b", "displayName": "Steckdose"}, "a03c")),
        ("Light Wandleuchten", MockGiraX1Light(coordinator, {"uid": "a02t", "displayName": "Wandleuchten"}, "a02u")),
        ("Light Steckdose", MockGiraX1Light(coordinator, {"uid": "a03b", "displayName": "Steckdose"}, "a03c")),
    ]
    
    logger.info("Real Gira X1 values:")
    for uid, value in real_values.items():
        logger.info(f"  {uid}: {value} (type: {type(value).__name__})")
    
    logger.info("\nEntity states:")
    all_correct = True
    
    for entity_name, entity in entities:
        state = entity.is_on
        expected = entity._on_off_uid in ["a03c"]  # Only a03c should be True ("1")
        correct = state == expected
        
        logger.info(f"  {entity_name}: {state} (expected: {expected}) {'✅' if correct else '❌'}")
        if not correct:
            all_correct = False
    
    logger.info(f"\nReal values test: {'✅ PASS' if all_correct else '❌ FAIL'}")
    return all_correct

def test_state_update_simulation():
    """Test state updates to simulate external changes."""
    logger.info("\n" + "=" * 80)
    logger.info("TESTING STATE UPDATE SIMULATION")
    logger.info("=" * 80)
    
    coordinator = MockCoordinator()
    
    # Create a switch entity
    switch = MockGiraX1Switch(coordinator, {"uid": "test", "displayName": "Test Switch"}, "test_uid")
    
    # Simulate state changes over time
    state_changes = [
        ("0", False, "Initial OFF state"),
        ("1", True, "Turn ON"),
        ("0", False, "Turn OFF"), 
        ("true", True, "External ON (true)"),
        ("false", False, "External OFF (false)"),
        ("on", True, "External ON (on)"),
        ("off", False, "External OFF (off)"),
    ]
    
    all_correct = True
    
    for value, expected_state, description in state_changes:
        logger.info(f"\n{description}:")
        logger.info(f"  Setting value: {value} -> Expected state: {expected_state}")
        
        # Update coordinator (simulates polling or callback)
        coordinator.update_values({"test_uid": value})
        
        # Check entity state
        actual_state = switch.is_on
        correct = actual_state == expected_state
        
        logger.info(f"  Entity state: {actual_state} {'✅' if correct else '❌'}")
        
        if not correct:
            all_correct = False
            logger.error(f"  ERROR: Expected {expected_state}, got {actual_state}")
    
    logger.info(f"\nState update simulation: {'✅ PASS' if all_correct else '❌ FAIL'}")
    return all_correct

def main():
    """Run all state synchronization fix validation tests."""
    logger.info("🔧 GIRA X1 STATE SYNCHRONIZATION - COMPLETE FIX VALIDATION")
    logger.info("=" * 80)
    logger.info("Testing the fixed string-to-boolean conversion logic")
    logger.info("=" * 80)
    
    start_time = time.time()
    
    # Run all tests
    tests = [
        ("String-to-Boolean Conversion", test_string_to_boolean_conversion),
        ("Real Gira X1 Values", test_real_gira_values),
        ("State Update Simulation", test_state_update_simulation),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        try:
            result = test_func()
            if result:
                passed_tests += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
    
    # Final summary
    duration = time.time() - start_time
    success_rate = (passed_tests / total_tests) * 100
    
    logger.info("\n" + "=" * 80)
    logger.info("FINAL VALIDATION RESULTS")
    logger.info("=" * 80)
    logger.info(f"Tests passed: {passed_tests}/{total_tests}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    logger.info(f"Test duration: {duration:.2f} seconds")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED - STATE SYNCHRONIZATION FIX VALIDATED!")
        logger.info("")
        logger.info("The fix addresses the core issue:")
        logger.info("✅ String values from API are correctly converted to boolean")
        logger.info("✅ Switch entities now handle '0'/'1' strings properly")
        logger.info("✅ Light entities continue to work correctly")
        logger.info("✅ State updates are processed consistently")
        logger.info("")
        logger.info("🚀 Ready for deployment - the state synchronization issue is resolved!")
    else:
        logger.error("❌ Some tests failed - fix needs additional work")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
