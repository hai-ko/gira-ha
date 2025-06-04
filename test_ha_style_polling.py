#!/usr/bin/env python3
"""
Simple Coordinator Test
======================

This script tests if the core polling logic is working correctly.
"""

import asyncio
import aiohttp
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

_LOGGER = logging.getLogger(__name__)

class SimpleGiraClient:
    """Simplified Gira client for testing."""
    
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.token = None
        self.session = None
        
    async def login(self):
        """Login to get token."""
        self.session = aiohttp.ClientSession()
        
        # Get token
        auth_url = f"https://{self.host}/api/v2/clients"
        auth_data = {
            "client": "Home Assistant Integration Test"
        }
        
        async with self.session.post(auth_url, json=auth_data, ssl=False) as response:
            if response.status == 200:
                result = await response.json()
                self.token = result.get("token")
                _LOGGER.info("✅ Successfully obtained token")
                return True
            else:
                _LOGGER.error("❌ Failed to get token: %s", response.status)
                return False
    
    async def get_value(self, uid):
        """Get value for a specific UID."""
        if not self.token:
            raise Exception("Not logged in")
        
        url = f"https://{self.host}/api/v2/values/{uid}"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        async with self.session.get(url, headers=headers, ssl=False) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("value")
            else:
                _LOGGER.warning(f"Failed to get value for {uid}: {response.status}")
                return None
    
    async def logout(self):
        """Logout and cleanup."""
        if self.session:
            await self.session.close()

class CoordinatorTest:
    """Test coordinator behavior."""
    
    def __init__(self, client):
        self.client = client
        self.last_values = {}
        
    async def poll_and_detect_changes(self, uids):
        """Poll UIDs and detect changes."""
        current_time = datetime.now().strftime("%H:%M:%S")
        _LOGGER.info(f"[{current_time}] Polling for values...")
        
        current_values = {}
        changes_detected = 0
        
        for uid in uids:
            try:
                value = await self.client.get_value(uid)
                current_values[uid] = value
                
                # Check for changes
                old_value = self.last_values.get(uid)
                if old_value is not None and old_value != value:
                    _LOGGER.info(f"🔄 CHANGE DETECTED: {uid}: '{old_value}' → '{value}'")
                    changes_detected += 1
                elif old_value is None:
                    _LOGGER.info(f"📍 INITIAL VALUE: {uid}: '{value}'")
                else:
                    _LOGGER.debug(f"   No change: {uid} = '{value}'")
                    
            except Exception as e:
                _LOGGER.warning(f"Failed to poll {uid}: {e}")
        
        # Update cache
        self.last_values.update(current_values)
        
        if changes_detected > 0:
            _LOGGER.info(f"📊 Total changes detected: {changes_detected}")
        else:
            _LOGGER.debug("No changes detected this cycle")
            
        return current_values, changes_detected

async def test_polling_behavior():
    """Test the polling behavior that should happen in Home Assistant."""
    _LOGGER.info("🚀 Testing Home Assistant-style Polling Behavior")
    _LOGGER.info("=" * 60)
    
    client = SimpleGiraClient("10.1.1.85", "admin", "admin")
    coordinator = CoordinatorTest(client)
    
    # Test UIDs
    test_uids = ["a02u", "a03c"]  # Wandleuchten and Steckdose
    
    try:
        # Login
        await client.login()
        
        _LOGGER.info("🔄 Starting 5-second polling cycles...")
        _LOGGER.info("This simulates what Home Assistant coordinator should do")
        _LOGGER.info("")
        
        total_changes = 0
        
        for cycle in range(1, 13):  # 1 minute of testing
            _LOGGER.info(f"📍 Cycle {cycle} at {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                values, changes = await coordinator.poll_and_detect_changes(test_uids)
                total_changes += changes
                
                # Log current state
                for uid in test_uids:
                    if uid in values:
                        _LOGGER.info(f"   {uid}: '{values[uid]}'")
                        
            except Exception as e:
                _LOGGER.error(f"Polling failed: {e}")
            
            if cycle < 12:
                _LOGGER.info("   ⏱️  Waiting 5 seconds...")
                await asyncio.sleep(5)
            
            _LOGGER.info("")
        
        _LOGGER.info(f"✅ Test completed. Total changes detected: {total_changes}")
        
        if total_changes == 0:
            _LOGGER.warning("⚠️  No changes detected during test period")
            _LOGGER.info("This could mean:")
            _LOGGER.info("1. No external changes occurred during test")
            _LOGGER.info("2. The devices are not being controlled externally")
            _LOGGER.info("3. There might be an issue with change detection")
        
    except Exception as e:
        _LOGGER.error(f"❌ Test failed: {e}", exc_info=True)
    finally:
        await client.logout()

if __name__ == "__main__":
    asyncio.run(test_polling_behavior())
