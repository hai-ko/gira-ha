#!/usr/bin/env python3
"""
Test polling behavior for specific UID "a0at"

This script demonstrates how the Gira X1 integration polls individual datapoints
when callback registration fails, specifically testing UID "a0at".

The integration polls each datapoint individually using:
GET /api/v2/values/{uid}
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Gira X1 Configuration
GIRA_HOST = "10.1.1.85"
GIRA_PORT = 443
GIRA_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"
TARGET_UID = "a0at"

class GiraX1PollingTest:
    """Test class for Gira X1 polling behavior."""
    
    def __init__(self):
        self.base_url = f"https://{GIRA_HOST}:{GIRA_PORT}"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification for self-signed cert
        self.session = aiohttp.ClientSession(connector=connector)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_value(self, uid: str) -> dict | None:
        """
        Get value for a specific UID using the same pattern as the integration.
        
        This mirrors the polling behavior in api.py:
        async def get_value(self, uid: str) -> dict | None:
            url = f"{self.base_url}/api/v2/values/{uid}"
        """
        url = f"{self.base_url}/api/v2/values/{uid}"
        headers = {
            "Authorization": f"Bearer {GIRA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Polling value for UID '{uid}' from: {url}")
            
            async with self.session.get(url, headers=headers) as response:
                logger.info(f"Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Successfully retrieved value for UID '{uid}': {data}")
                    return data
                elif response.status == 404:
                    logger.warning(f"UID '{uid}' not found (404)")
                    return None
                else:
                    error_text = await response.text()
                    logger.error(f"Error {response.status}: {error_text}")
                    return None
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error polling UID '{uid}': {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for UID '{uid}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error polling UID '{uid}': {e}")
            return None
    
    async def get_all_values(self) -> dict:
        """
        Get all values using the batch endpoint.
        
        This is used by the integration to get initial data and during polling updates.
        """
        url = f"{self.base_url}/api/v2/values"
        headers = {
            "Authorization": f"Bearer {GIRA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Getting all values from: {url}")
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Retrieved {len(data)} total values")
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Error getting all values {response.status}: {error_text}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting all values: {e}")
            return {}
    
    async def test_uid_a0at_polling(self):
        """Test polling behavior specifically for UID 'a0at'."""
        
        logger.info("=" * 80)
        logger.info("GIRA X1 POLLING TEST FOR UID 'a0at'")
        logger.info("=" * 80)
        logger.info(f"Target: https://{GIRA_HOST}:{GIRA_PORT}")
        logger.info(f"UID: {TARGET_UID}")
        logger.info(f"Token: {GIRA_TOKEN[:10]}...")
        logger.info("=" * 80)
        
        # Test 1: Check if UID exists in all values
        logger.info("\n--- Test 1: Check UID existence in batch values ---")
        all_values = await self.get_all_values()
        
        if TARGET_UID in all_values:
            logger.info(f"✅ UID '{TARGET_UID}' found in batch values")
            logger.info(f"Value from batch: {all_values[TARGET_UID]}")
        else:
            logger.warning(f"❌ UID '{TARGET_UID}' NOT found in batch values")
            logger.info(f"Available UIDs: {list(all_values.keys())[:10]}... (showing first 10)")
            
            # Try to find similar UIDs
            similar_uids = [uid for uid in all_values.keys() if 'a0' in uid or 'at' in uid]
            if similar_uids:
                logger.info(f"Similar UIDs found: {similar_uids}")
        
        # Test 2: Direct polling of the specific UID
        logger.info(f"\n--- Test 2: Direct polling of UID '{TARGET_UID}' ---")
        value = await self.get_value(TARGET_UID)
        
        if value is not None:
            logger.info(f"✅ Successfully polled UID '{TARGET_UID}'")
            logger.info(f"Direct poll result: {value}")
        else:
            logger.warning(f"❌ Failed to poll UID '{TARGET_UID}'")
        
        # Test 3: Continuous polling simulation (like the integration does)
        logger.info(f"\n--- Test 3: Continuous polling simulation (5 cycles) ---")
        logger.info("This simulates the 5-second polling when callbacks fail...")
        
        for cycle in range(1, 6):
            logger.info(f"\nPolling cycle {cycle}/5:")
            start_time = datetime.now()
            
            # This is what the integration does in polling mode
            cycle_value = await self.get_value(TARGET_UID)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if cycle_value is not None:
                logger.info(f"  ✅ Cycle {cycle}: Success in {duration:.2f}s - Value: {cycle_value}")
            else:
                logger.info(f"  ❌ Cycle {cycle}: Failed in {duration:.2f}s")
            
            # Wait 5 seconds between polls (like the integration)
            if cycle < 5:
                logger.info("  ⏳ Waiting 5 seconds for next poll...")
                await asyncio.sleep(5)
        
        logger.info("\n" + "=" * 80)
        logger.info("POLLING TEST COMPLETE")
        logger.info("=" * 80)
        
        # Summary
        logger.info("\n--- SUMMARY ---")
        logger.info(f"UID '{TARGET_UID}' status:")
        if TARGET_UID in all_values:
            logger.info(f"  ✅ Found in batch values: {all_values[TARGET_UID]}")
        else:
            logger.info(f"  ❌ Not found in batch values")
            
        if value is not None:
            logger.info(f"  ✅ Direct polling successful: {value}")
        else:
            logger.info(f"  ❌ Direct polling failed")
        
        logger.info("\nThis demonstrates how the Gira X1 integration polls individual")
        logger.info("datapoints when callback registration fails, using 5-second intervals.")


async def main():
    """Main test function."""
    try:
        async with GiraX1PollingTest() as test:
            await test.test_uid_a0at_polling()
            
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
