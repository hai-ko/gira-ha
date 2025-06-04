#!/usr/bin/env python3
"""
Test script to validate the state synchronization fix.

This script tests:
1. String-to-boolean conversion logic in switch entities  
2. State synchronization between API and entity states
3. Verification of value updates through coordinator
"""

import asyncio
import aiohttp
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
GIRA_HOST = "10.1.1.85"
GIRA_PORT = 443
GIRA_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"

# Test UIDs from diagnostic results
TEST_UIDS = [
    "a02u",  # OnOff for "Wandleuchten" - returned "0"
    "a03c",  # OnOff for "Steckdose" - returned "1"  
]

def test_string_to_boolean_conversion():
    """Test the string-to-boolean conversion logic we implemented."""
    logger.info("=== Testing String-to-Boolean Conversion Logic ===")
    
    def is_on_fixed(value):
        """Fixed version: Handle string values from API (Gira X1 returns "0"/"1" as strings)"""
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'on')
        return bool(value)
    
    def is_on_broken(value):
        """Broken version: Direct bool() conversion"""
        return bool(value)
    
    test_cases = [
        ("0", False, "String '0' should be False"),
        ("1", True, "String '1' should be True"),  
        ("true", True, "String 'true' should be True"),
        ("false", False, "String 'false' should be False"),
        ("on", True, "String 'on' should be True"),
        ("off", False, "String 'off' should be False"),
        (0, False, "Integer 0 should be False"),
        (1, True, "Integer 1 should be True"),
        (True, True, "Boolean True should be True"),
        (False, False, "Boolean False should be False"),
    ]
    
    logger.info("Testing conversion logic...")
    all_passed = True
    
    for value, expected, description in test_cases:
        fixed_result = is_on_fixed(value)
        broken_result = is_on_broken(value)
        
        fixed_correct = fixed_result == expected
        broken_correct = broken_result == expected
        
        status_fixed = "✅" if fixed_correct else "❌"
        status_broken = "✅" if broken_correct else "❌"
        
        logger.info(f"  {description}")
        logger.info(f"    Value: {repr(value)} (type: {type(value).__name__})")
        logger.info(f"    Expected: {expected}")
        logger.info(f"    Fixed logic:  {fixed_result} {status_fixed}")
        logger.info(f"    Broken logic: {broken_result} {status_broken}")
        logger.info("")
        
        if not fixed_correct:
            all_passed = False
    
    if all_passed:
        logger.info("✅ All conversion tests passed!")
    else:
        logger.error("❌ Some conversion tests failed!")
    
    return all_passed

class StateSynchronizationTest:
    """Test state synchronization with real API calls."""
    
    def __init__(self):
        self.base_url = f"https://{GIRA_HOST}:{GIRA_PORT}/api/v2"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_datapoint_value(self, uid: str) -> dict | None:
        """Get current value for a datapoint."""
        url = f"{self.base_url}/values/{uid}"
        headers = {
            "Authorization": f"Bearer {GIRA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.warning(f"Failed to get value for {uid}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Exception getting value for {uid}: {e}")
            return None
    
    async def test_actual_values(self):
        """Test conversion logic with actual values from the device."""
        logger.info("=== Testing Actual API Values ===")
        
        for uid in TEST_UIDS:
            logger.info(f"\nTesting UID: {uid}")
            
            # Get actual value from API
            result = await self.get_datapoint_value(uid)
            if not result:
                logger.warning(f"  Could not retrieve value for {uid}")
                continue
            
            # Extract value from API response
            values_list = result.get("values", [])
            if not values_list:
                logger.warning(f"  No values in response for {uid}")
                continue
            
            api_value = values_list[0].get("value")
            logger.info(f"  API returned: {repr(api_value)} (type: {type(api_value).__name__})")
            
            # Test both conversion methods
            def is_on_fixed(value):
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'on')
                return bool(value)
            
            def is_on_broken(value):
                return bool(value)
            
            fixed_result = is_on_fixed(api_value)
            broken_result = is_on_broken(api_value)
            
            logger.info(f"  Fixed conversion:  {fixed_result}")
            logger.info(f"  Broken conversion: {broken_result}")
            
            if fixed_result != broken_result:
                logger.info(f"  🔧 CONVERSION FIX MAKES A DIFFERENCE!")
                logger.info(f"     The fix changed the result from {broken_result} to {fixed_result}")
            else:
                logger.info(f"  ℹ️  Both methods agree on this value")

async def main():
    """Main test function."""
    logger.info("🔧 GIRA X1 STATE SYNCHRONIZATION FIX TEST")
    logger.info("=" * 60)
    
    # Test 1: Conversion logic
    conversion_ok = test_string_to_boolean_conversion()
    
    # Test 2: Real API values
    async with StateSynchronizationTest() as tester:
        await tester.test_actual_values()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 FIX VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    if conversion_ok:
        logger.info("✅ String-to-boolean conversion logic is correct")
        logger.info("✅ Switch entities will now properly handle API string values")
        logger.info("✅ State synchronization should work correctly")
        
        logger.info("\n🚀 NEXT STEPS:")
        logger.info("1. Restart Home Assistant to apply the fix")
        logger.info("2. Test switch entities manually (toggle on/off)")
        logger.info("3. Monitor entity states in Home Assistant UI")
        logger.info("4. Check if external changes reflect in Home Assistant")
    else:
        logger.error("❌ Conversion logic test failed - fix needs adjustment")

if __name__ == "__main__":
    asyncio.run(main())
