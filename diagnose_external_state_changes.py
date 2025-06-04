#!/usr/bin/env python3
"""
REAL-TIME GIRA X1 STATE CHANGE DIAGNOSIS
======================================

This script will diagnose what's happening with external state changes
by monitoring the actual Gira X1 device and checking:
1. Are callbacks being registered successfully?
2. Is polling happening as expected?
3. Are external changes reflected in the API?
4. What's the current coordinator behavior?
"""

import asyncio
import aiohttp
import logging
import json
import ssl
from datetime import datetime
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Gira X1 Configuration
GIRA_HOST = "10.1.1.85"
GIRA_PORT = 443
GIRA_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"

class GiraX1StateMonitor:
    """Monitor Gira X1 state changes in real-time."""
    
    def __init__(self, host: str, token: str):
        self.host = host
        self.token = token
        self.base_url = f"https://{host}"
        self.headers = {"Authorization": f"Bearer {token}"}
        
        # SSL context that ignores certificate verification
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Track state
        self.previous_values = {}
        self.callback_status = None
    
    async def check_callback_status(self) -> Dict[str, Any]:
        """Check if callbacks are currently registered."""
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context)) as session:
            try:
                url = f"{self.base_url}/api/v2/callbacks"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        callbacks = await response.json()
                        return {"success": True, "callbacks": callbacks}
                    else:
                        return {"success": False, "status": response.status}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def get_datapoint_value(self, uid: str) -> Optional[str]:
        """Get current value for a specific datapoint."""
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context)) as session:
            try:
                url = f"{self.base_url}/api/v2/values/{uid}"
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        values = data.get("values", [])
                        if values:
                            return values[0].get("value")
                    return None
            except Exception as e:
                logger.error(f"Error getting value for {uid}: {e}")
                return None
    
    async def monitor_key_datapoints(self, poll_interval: int = 5):
        """Monitor key datapoints for state changes."""
        # Key datapoints to monitor
        datapoints = {
            "a02u": "Wandleuchten (Switch)",
            "a03c": "Steckdose (Switch)",
        }
        
        logger.info("🔧 REAL-TIME GIRA X1 STATE CHANGE MONITORING")
        logger.info("=" * 80)
        logger.info("Monitoring key datapoints for external state changes...")
        logger.info("Press Ctrl+C to stop monitoring")
        logger.info("")
        
        # Check initial callback status
        callback_info = await self.check_callback_status()
        if callback_info["success"]:
            callbacks = callback_info.get("callbacks", [])
            logger.info(f"📞 Callback Status: {len(callbacks)} callbacks registered")
            for cb in callbacks:
                logger.info(f"   - {cb.get('event_type', 'unknown')}: {cb.get('url', 'no URL')}")
        else:
            logger.info(f"📞 Callback Status: Failed to check - {callback_info}")
        logger.info("")
        
        cycle_count = 0
        state_changes = []
        
        try:
            while True:
                cycle_count += 1
                current_time = datetime.now().strftime("%H:%M:%S")
                logger.info(f"🔄 Polling Cycle {cycle_count} at {current_time}")
                
                current_values = {}
                changes_detected = False
                
                # Poll each datapoint
                for uid, name in datapoints.items():
                    value = await self.get_datapoint_value(uid)
                    current_values[uid] = value
                    
                    # Check for changes
                    previous_value = self.previous_values.get(uid)
                    if previous_value != value:
                        change_info = {
                            "timestamp": current_time,
                            "uid": uid,
                            "datapoint": name,
                            "old_value": previous_value,
                            "new_value": value
                        }
                        state_changes.append(change_info)
                        changes_detected = True
                        logger.info(f"   🔄 CHANGE DETECTED: {name} ({uid}): '{previous_value}' → '{value}'")
                    else:
                        logger.info(f"   ℹ️  No change: {name} ({uid}) = '{value}'")
                
                # Update previous values
                self.previous_values = current_values.copy()
                
                if not changes_detected:
                    logger.info("   📊 No changes detected in this cycle")
                
                # Status summary
                logger.info(f"   📈 Total changes detected so far: {len(state_changes)}")
                logger.info(f"   ⏱️  Next poll in {poll_interval} seconds...")
                logger.info("")
                
                # Wait for next cycle
                await asyncio.sleep(poll_interval)
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 80)
            logger.info("MONITORING STOPPED")
            logger.info("=" * 80)
            
            # Summary
            logger.info(f"📊 Total polling cycles: {cycle_count}")
            logger.info(f"📈 Total state changes detected: {len(state_changes)}")
            
            if state_changes:
                logger.info("\n🔄 Detected state changes:")
                for i, change in enumerate(state_changes, 1):
                    logger.info(f"  {i}. {change['datapoint']} ({change['uid']}): "
                              f"'{change['old_value']}' → '{change['new_value']}' at {change['timestamp']}")
                logger.info("\n✅ CONCLUSION: External state changes ARE detected by API polling!")
                logger.info("   If Home Assistant isn't reflecting these changes, the issue is likely:")
                logger.info("   - Coordinator update logic not working properly")
                logger.info("   - Entity state refresh not happening")
                logger.info("   - Callback system interfering with polling updates")
            else:
                logger.info("\n📊 No state changes detected during monitoring period")
                logger.info("   This could mean:")
                logger.info("   - No external changes were made during monitoring")
                logger.info("   - Devices were not physically toggled")
                logger.info("   - API polling is working but no changes occurred")
            
            # Final state summary
            logger.info(f"\n📋 Final states:")
            for uid, name in datapoints.items():
                final_value = self.previous_values.get(uid)
                logger.info(f"  {name} ({uid}): '{final_value}'")

async def main():
    """Run real-time state change monitoring."""
    logger.info("🚀 Starting Gira X1 Real-Time State Change Monitoring...")
    logger.info("This will help diagnose why external changes aren't reflected in Home Assistant")
    logger.info("")
    
    monitor = GiraX1StateMonitor(GIRA_HOST, GIRA_TOKEN)
    await monitor.monitor_key_datapoints()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMonitoring interrupted by user")
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")
