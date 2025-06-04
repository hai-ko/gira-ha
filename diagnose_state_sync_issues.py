#!/usr/bin/env python3
"""
Comprehensive test to diagnose state synchronization issues.

This script will:
1. Test API polling to see what data is actually returned
2. Check if values change when polled multiple times
3. Test external state changes detection
4. Analyze data format and parsing
5. Verify coordinator data flow
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Gira X1 Configuration
GIRA_HOST = "10.1.1.85"
GIRA_PORT = 443
GIRA_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"

class StateDebugger:
    """Debug state synchronization issues."""
    
    def __init__(self):
        self.base_url = f"https://{GIRA_HOST}:{GIRA_PORT}"
        self.session = None
        self.ui_config = None
        self.datapoint_cache = {}
        
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration to understand device structure."""
        url = f"{self.base_url}/api/v2/uiconfig"
        headers = {
            "Authorization": f"Bearer {GIRA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved UI config with {len(data.get('functions', []))} functions")
                    return data
                else:
                    logger.error(f"Failed to get UI config: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Exception getting UI config: {e}")
            return {}
    
    async def get_datapoint_value(self, uid: str) -> Dict[str, Any] | None:
        """Get value for a specific datapoint."""
        url = f"{self.base_url}/api/values/{uid}"
        headers = {
            "Authorization": f"Bearer {GIRA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 404:
                    logger.debug(f"Datapoint {uid} not found (404)")
                    return None
                else:
                    logger.warning(f"Error getting value for {uid}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Exception getting value for {uid}: {e}")
            return None
    
    async def set_datapoint_value(self, uid: str, value: Any) -> bool:
        """Set value for a specific datapoint."""
        url = f"{self.base_url}/api/values/{uid}"
        headers = {
            "Authorization": f"Bearer {GIRA_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {"value": value}
        
        try:
            async with self.session.put(url, headers=headers, json=data) as response:
                if response.status == 200:
                    logger.info(f"Successfully set {uid} = {value}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to set {uid}: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"Exception setting {uid}: {e}")
            return False
    
    async def analyze_functions_and_datapoints(self):
        """Analyze all functions and their datapoints."""
        logger.info("=" * 80)
        logger.info("ANALYZING FUNCTIONS AND DATAPOINTS")
        logger.info("=" * 80)
        
        self.ui_config = await self.get_ui_config()
        functions = self.ui_config.get("functions", [])
        
        if not functions:
            logger.error("No functions found in UI config!")
            return
        
        logger.info(f"Found {len(functions)} functions")
        
        # Analyze first few functions in detail
        sample_functions = functions[:5]
        for i, func in enumerate(sample_functions):
            logger.info(f"\n--- Function {i+1}: {func.get('displayName', 'Unknown')} ---")
            logger.info(f"UID: {func.get('uid')}")
            logger.info(f"Function Type: {func.get('functionType')}")
            logger.info(f"Channel Type: {func.get('channelType')}")
            
            datapoints = func.get("dataPoints", [])
            logger.info(f"Datapoints ({len(datapoints)}):")
            
            for dp in datapoints:
                dp_name = dp.get("name", "Unknown")
                dp_uid = dp.get("uid", "Unknown")
                dp_flags = dp.get("flags", [])
                
                logger.info(f"  - {dp_name} ({dp_uid}) flags: {dp_flags}")
                
                # Cache datapoint for later testing
                self.datapoint_cache[dp_uid] = {
                    "name": dp_name,
                    "function_uid": func.get("uid"),
                    "function_name": func.get("displayName"),
                    "flags": dp_flags
                }
    
    async def test_datapoint_polling(self, max_datapoints: int = 10):
        """Test polling of actual datapoints."""
        logger.info("\n" + "=" * 80)
        logger.info("TESTING DATAPOINT POLLING")
        logger.info("=" * 80)
        
        # Get a sample of datapoints to test
        test_datapoints = list(self.datapoint_cache.keys())[:max_datapoints]
        
        logger.info(f"Testing {len(test_datapoints)} datapoints:")
        
        successful_reads = []
        failed_reads = []
        
        for dp_uid in test_datapoints:
            dp_info = self.datapoint_cache[dp_uid]
            logger.info(f"\nTesting datapoint: {dp_info['name']} ({dp_uid})")
            logger.info(f"  Function: {dp_info['function_name']} ({dp_info['function_uid']})")
            logger.info(f"  Flags: {dp_info['flags']}")
            
            # Test reading the value
            result = await self.get_datapoint_value(dp_uid)
            
            if result:
                values = result.get("values", [])
                if values and len(values) > 0:
                    value = values[0].get("value")
                    logger.info(f"  ✅ Success: {value} (type: {type(value).__name__})")
                    successful_reads.append({
                        "uid": dp_uid,
                        "name": dp_info['name'],
                        "value": value,
                        "raw_response": result
                    })
                else:
                    logger.warning(f"  ⚠️ Empty values array in response: {result}")
                    failed_reads.append(dp_uid)
            else:
                logger.warning(f"  ❌ Failed to read")
                failed_reads.append(dp_uid)
        
        logger.info(f"\n--- POLLING SUMMARY ---")
        logger.info(f"Successful reads: {len(successful_reads)}")
        logger.info(f"Failed reads: {len(failed_reads)}")
        
        return successful_reads, failed_reads
    
    async def test_state_changes(self, test_datapoints: list):
        """Test if we can detect state changes."""
        logger.info("\n" + "=" * 80)
        logger.info("TESTING STATE CHANGE DETECTION")
        logger.info("=" * 80)
        
        if not test_datapoints:
            logger.warning("No readable datapoints to test state changes")
            return
        
        # Find a writable datapoint (has write flag)
        writable_dp = None
        for dp in test_datapoints:
            dp_uid = dp["uid"]
            dp_info = self.datapoint_cache[dp_uid]
            flags = dp_info.get("flags", [])
            
            # Look for write flag
            has_write = any("write" in str(flag).lower() for flag in flags)
            if has_write:
                writable_dp = dp
                break
        
        if not writable_dp:
            logger.warning("No writable datapoints found for state change testing")
            
            # Show all datapoints and their flags
            logger.info("Available datapoints and flags:")
            for dp in test_datapoints:
                dp_uid = dp["uid"]
                dp_info = self.datapoint_cache[dp_uid]
                logger.info(f"  {dp_info['name']} ({dp_uid}): {dp_info['flags']}")
            return
        
        dp_uid = writable_dp["uid"]
        dp_info = self.datapoint_cache[dp_uid]
        original_value = writable_dp["value"]
        
        logger.info(f"Testing state changes on: {dp_info['name']} ({dp_uid})")
        logger.info(f"Original value: {original_value} (type: {type(original_value).__name__})")
        
        # Determine what values to test based on current value type
        if isinstance(original_value, bool) or str(original_value).lower() in ['true', 'false', '0', '1']:
            test_values = [True, False] if original_value != True else [False, True]
        elif isinstance(original_value, (int, float)) or str(original_value).isdigit():
            current_num = float(original_value)
            test_values = [0, 100] if current_num != 0 else [100, 0]
        else:
            logger.warning(f"Don't know how to test changes for value type: {type(original_value).__name__}")
            return
        
        logger.info(f"Will test with values: {test_values}")
        
        for i, test_value in enumerate(test_values):
            logger.info(f"\n--- Change Test {i+1}: Setting to {test_value} ---")
            
            # Set the new value
            success = await self.set_datapoint_value(dp_uid, test_value)
            if not success:
                logger.error(f"Failed to set value to {test_value}")
                continue
            
            # Wait a moment for the change to propagate
            await asyncio.sleep(2)
            
            # Read the value back multiple times to see if polling detects the change
            for poll_attempt in range(3):
                logger.info(f"  Poll attempt {poll_attempt + 1}:")
                result = await self.get_datapoint_value(dp_uid)
                
                if result and result.get("values"):
                    current_value = result["values"][0].get("value")
                    logger.info(f"    Read value: {current_value} (type: {type(current_value).__name__})")
                    
                    # Check if the value matches what we set
                    if str(current_value) == str(test_value):
                        logger.info(f"    ✅ Value matches what we set!")
                    else:
                        logger.warning(f"    ❌ Value doesn't match! Expected {test_value}, got {current_value}")
                else:
                    logger.error(f"    ❌ Failed to read value back")
                
                if poll_attempt < 2:
                    await asyncio.sleep(1)
        
        # Restore original value
        logger.info(f"\n--- Restoring original value: {original_value} ---")
        await self.set_datapoint_value(dp_uid, original_value)
    
    async def test_polling_consistency(self, test_datapoints: list, cycles: int = 5):
        """Test if polling returns consistent results."""
        logger.info("\n" + "=" * 80)
        logger.info(f"TESTING POLLING CONSISTENCY ({cycles} cycles)")
        logger.info("=" * 80)
        
        if not test_datapoints:
            logger.warning("No datapoints to test consistency")
            return
        
        # Pick a few datapoints to test
        test_sample = test_datapoints[:3]
        
        for dp in test_sample:
            dp_uid = dp["uid"]
            dp_info = self.datapoint_cache[dp_uid]
            
            logger.info(f"\nTesting consistency for: {dp_info['name']} ({dp_uid})")
            
            values_over_time = []
            
            for cycle in range(cycles):
                result = await self.get_datapoint_value(dp_uid)
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                
                if result and result.get("values"):
                    value = result["values"][0].get("value")
                    values_over_time.append((timestamp, value))
                    logger.info(f"  Cycle {cycle + 1} ({timestamp}): {value}")
                else:
                    logger.error(f"  Cycle {cycle + 1}: Failed to read")
                
                if cycle < cycles - 1:
                    await asyncio.sleep(2)
            
            # Analyze consistency
            unique_values = set(v[1] for v in values_over_time if v[1] is not None)
            if len(unique_values) == 1:
                logger.info(f"  ✅ Values consistent: {list(unique_values)[0]}")
            else:
                logger.warning(f"  ⚠️ Values changed: {list(unique_values)}")
                for timestamp, value in values_over_time:
                    logger.info(f"    {timestamp}: {value}")
    
    async def run_comprehensive_diagnosis(self):
        """Run comprehensive state synchronization diagnosis."""
        logger.info("🔧 GIRA X1 STATE SYNCHRONIZATION DIAGNOSIS")
        logger.info("=" * 80)
        logger.info(f"Target: {self.base_url}")
        logger.info(f"Token: {GIRA_TOKEN[:10]}...")
        logger.info("=" * 80)
        
        # Step 1: Analyze device structure
        await self.analyze_functions_and_datapoints()
        
        if not self.datapoint_cache:
            logger.error("No datapoints found! Cannot continue diagnosis.")
            return
        
        # Step 2: Test basic polling
        successful_reads, failed_reads = await self.test_datapoint_polling()
        
        # Step 3: Test state change detection
        await self.test_state_changes(successful_reads)
        
        # Step 4: Test polling consistency
        await self.test_polling_consistency(successful_reads)
        
        # Step 5: Summary and recommendations
        logger.info("\n" + "=" * 80)
        logger.info("DIAGNOSIS SUMMARY")
        logger.info("=" * 80)
        
        total_datapoints = len(self.datapoint_cache)
        successful_count = len(successful_reads)
        failed_count = len(failed_reads)
        
        logger.info(f"Total datapoints found: {total_datapoints}")
        logger.info(f"Successfully readable: {successful_count}")
        logger.info(f"Failed to read: {failed_count}")
        logger.info(f"Read success rate: {successful_count/max(1, successful_count + failed_count)*100:.1f}%")
        
        if successful_count == 0:
            logger.error("❌ CRITICAL: No datapoints are readable!")
            logger.error("   - Check API permissions")
            logger.error("   - Verify datapoint flags")
            logger.error("   - Check device configuration")
        elif failed_count > successful_count:
            logger.warning("⚠️ WARNING: Many datapoints failed to read")
            logger.warning("   - Some entities may not work correctly")
            logger.warning("   - Check datapoint configuration")
        else:
            logger.info("✅ GOOD: Most datapoints are readable")
        
        logger.info("\nRECOMMENDations:")
        logger.info("1. Check that entities are using the correct datapoint UIDs")
        logger.info("2. Verify that polling interval is appropriate (currently 5 seconds)")
        logger.info("3. Ensure entities refresh their state when coordinator data changes")
        logger.info("4. Check that value parsing handles all data types correctly")


async def main():
    """Main diagnosis function."""
    try:
        async with StateDebugger() as debugger:
            await debugger.run_comprehensive_diagnosis()
    except KeyboardInterrupt:
        logger.info("\nDiagnosis interrupted by user")
    except Exception as e:
        logger.error(f"Diagnosis failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
