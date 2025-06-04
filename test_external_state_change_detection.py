#!/usr/bin/env python3
"""
GIRA X1 EXTERNAL STATE CHANGE DETECTION DIAGNOSIS
================================================

This script diagnoses why external state changes are not being reflected in Home Assistant.
It will:
1. Simulate continuous polling like the integration
2. Monitor for state changes when you manually toggle devices
3. Check if the API is returning updated values
4. Identify if the issue is with polling frequency, callback system, or integration logic
"""

import asyncio
import logging
import json
import time
import ssl
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GiraX1ExternalChangeMonitor:
    """Monitor for external state changes on Gira X1."""
    
    def __init__(self, host: str, token: str):
        self.host = host
        self.token = token
        self.base_url = f"https://{host}"
        self.headers = {"Authorization": f"Bearer {token}"}
        
        # SSL context that ignores certificate verification (like the integration)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Track state changes
        self.previous_values = {}
        self.state_changes = []
        
    async def get_datapoint_value(self, uid: str) -> Optional[str]:
        """Get current value for a specific datapoint."""
        url = f"{self.base_url}/api/v2/values/{uid}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, ssl=self.ssl_context) as response:
                    if response.status == 200:
                        data = await response.json()
                        values_list = data.get("values", [])
                        for value_item in values_list:
                            if value_item.get("uid") == uid and "value" in value_item:
                                return value_item["value"]
                    else:
                        logger.warning(f"Failed to get value for {uid}: HTTP {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Error getting value for {uid}: {e}")
                return None
    
    async def monitor_datapoints(self, datapoints: Dict[str, str], poll_interval: int = 5):
        """Monitor specific datapoints for state changes."""
        logger.info("=" * 80)
        logger.info("STARTING EXTERNAL STATE CHANGE MONITORING")
        logger.info("=" * 80)
        logger.info(f"Monitoring {len(datapoints)} datapoints:")
        for uid, name in datapoints.items():
            logger.info(f"  - {name} ({uid})")
        logger.info(f"Poll interval: {poll_interval} seconds")
        logger.info(f"Host: {self.host}")
        logger.info("")
        
        # Get initial states
        logger.info("Getting initial states...")
        for uid, name in datapoints.items():
            value = await self.get_datapoint_value(uid)
            self.previous_values[uid] = value
            logger.info(f"  {name} ({uid}): {value}")
        
        logger.info("")
        logger.info("🔍 MONITORING STARTED - Please manually change device states now...")
        logger.info("   (flip switches, change lights, etc.)")
        logger.info("   Press Ctrl+C to stop monitoring")
        logger.info("")
        
        cycle_count = 0
        try:
            while True:
                cycle_count += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                logger.info(f"--- Polling Cycle {cycle_count} at {current_time} ---")
                
                changes_detected = False
                
                # Check each datapoint for changes
                for uid, name in datapoints.items():
                    current_value = await self.get_datapoint_value(uid)
                    previous_value = self.previous_values.get(uid)
                    
                    if current_value != previous_value:
                        changes_detected = True
                        change_info = {
                            "timestamp": current_time,
                            "datapoint": name,
                            "uid": uid,
                            "old_value": previous_value,
                            "new_value": current_value
                        }
                        self.state_changes.append(change_info)
                        
                        logger.info(f"🔥 STATE CHANGE DETECTED!")
                        logger.info(f"   Datapoint: {name} ({uid})")
                        logger.info(f"   Old value: {previous_value}")
                        logger.info(f"   New value: {current_value}")
                        logger.info(f"   Time: {current_time}")
                        
                        # Update tracked value
                        self.previous_values[uid] = current_value
                    else:
                        logger.debug(f"   {name}: {current_value} (no change)")
                
                if not changes_detected:
                    logger.info("   No changes detected in this cycle")
                
                # Wait for next poll
                logger.info(f"   Waiting {poll_interval} seconds for next poll...")
                await asyncio.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 80)
            logger.info("MONITORING STOPPED")
            logger.info("=" * 80)
            
            # Summary
            logger.info(f"Total polling cycles: {cycle_count}")
            logger.info(f"Total state changes detected: {len(self.state_changes)}")
            
            if self.state_changes:
                logger.info("\nDetected state changes:")
                for i, change in enumerate(self.state_changes, 1):
                    logger.info(f"  {i}. {change['datapoint']} ({change['uid']}): "
                              f"{change['old_value']} → {change['new_value']} at {change['timestamp']}")
                logger.info("\n✅ SUCCESS: External state changes ARE being detected by API polling!")
                logger.info("   If Home Assistant isn't reflecting these changes, the issue is likely:")
                logger.info("   - Coordinator not polling frequently enough")
                logger.info("   - Callback system interfering with polling")
                logger.info("   - Entity state refresh not working properly")
            else:
                logger.info("\n❌ No state changes detected during monitoring period")
                logger.info("   This could mean:")
                logger.info("   - No external changes were made during monitoring")
                logger.info("   - API is not returning updated values")
                logger.info("   - Datapoints selected don't support external changes")
            
            # Final state summary
            logger.info("\nFinal states:")
            for uid, name in datapoints.items():
                final_value = self.previous_values.get(uid)
                logger.info(f"  {name} ({uid}): {final_value}")

async def main():
    """Run external state change monitoring."""
    # Gira X1 connection details
    HOST = "10.1.1.85"
    TOKEN = "t3jwcfrqIAJYRJ1SIAGaJQXzUIIIJfmN"
    
    # Key datapoints to monitor (from previous diagnostic)
    DATAPOINTS_TO_MONITOR = {
        "a02u": "Wandleuchten (Switch)",       # Should be controllable
        "a03c": "Steckdose (Switch)",          # Should be controllable  
        "a060": "Fenster 1 Position",         # Might be controllable
        "a061": "Fenster 1 Slat Position",    # Might be controllable
    }
    
    logger.info("🔧 GIRA X1 EXTERNAL STATE CHANGE DETECTION DIAGNOSIS")
    logger.info("=" * 80)
    logger.info("This tool will monitor for external state changes in real-time")
    logger.info("to determine if the API reflects external device changes.")
    logger.info("")
    logger.info("Please follow these steps:")
    logger.info("1. Start this monitoring tool")
    logger.info("2. Manually change device states (physical switches, app, etc.)")
    logger.info("3. Observe if changes are detected")
    logger.info("4. Stop monitoring with Ctrl+C")
    logger.info("")
    
    monitor = GiraX1ExternalChangeMonitor(HOST, TOKEN)
    
    # Monitor with 5-second intervals (same as integration default)
    await monitor.monitor_datapoints(DATAPOINTS_TO_MONITOR, poll_interval=5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMonitoring interrupted by user")
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")
        exit(1)
