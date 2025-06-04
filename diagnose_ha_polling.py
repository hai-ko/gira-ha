#!/usr/bin/env python3
"""
Diagnose Home Assistant Polling Behavior
========================================

This script directly tests the coordinator logic to see if it's working correctly
without requiring the full Home Assistant environment.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the custom component path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

# Mock Home Assistant components to avoid import errors
class MockHomeAssistant:
    def __init__(self):
        self.data = {}
        self.bus = None
        
class MockConfigEntry:
    def __init__(self):
        self.entry_id = "test_entry"
        
class MockDataUpdateCoordinator:
    def __init__(self, hass, logger, name, update_interval):
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self._listeners = []
        
    async def async_request_refresh(self):
        """Mock refresh."""
        pass

# Mock the HomeAssistant modules
sys.modules['homeassistant.core'] = type('MockModule', (), {
    'HomeAssistant': MockHomeAssistant,
    'callback': lambda x: x,
})()

sys.modules['homeassistant.config_entries'] = type('MockModule', (), {
    'ConfigEntry': MockConfigEntry,
})()

sys.modules['homeassistant.helpers.update_coordinator'] = type('MockModule', (), {
    'DataUpdateCoordinator': MockDataUpdateCoordinator,
    'UpdateFailed': Exception,
})()

sys.modules['homeassistant.helpers'] = type('MockModule', (), {})()
sys.modules['homeassistant.helpers.service'] = type('MockModule', (), {})()
sys.modules['homeassistant.const'] = type('MockModule', (), {})()

import voluptuous as vol
sys.modules['homeassistant.helpers.config_validation'] = vol

# Now import our components
from gira_x1.api import GiraX1Client
from gira_x1.const import UPDATE_INTERVAL_SECONDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

_LOGGER = logging.getLogger(__name__)

class MockCoordinator:
    """Mock coordinator that mimics the real behavior."""
    
    def __init__(self, client):
        self.client = client
        self.callbacks_enabled = False
        self._last_values = {}
        self.functions = {}
        self.ui_config = {}
        self.ui_config_uid = None
        
    async def _async_update_data(self):
        """Update data via library - copied from real coordinator."""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            if self.callbacks_enabled:
                _LOGGER.debug("[%s] Starting data update cycle (callbacks registered, but polling for reliability)", current_time)
            else:
                _LOGGER.debug("[%s] Starting data update cycle (polling mode)", current_time)
            
            # Check if UI config has changed
            current_uid = await self.client.get_ui_config_uid()
            _LOGGER.debug("Current UI config UID: %s, cached UID: %s", current_uid, self.ui_config_uid)
            
            if current_uid != self.ui_config_uid:
                _LOGGER.info("UI configuration changed (UID: %s), refreshing full config...", current_uid)
                # Get full UI configuration with expanded data point flags
                self.ui_config = await self.client.get_ui_config(
                    expand=["dataPointFlags", "parameters"]
                )
                self.ui_config_uid = current_uid
                
                # Update functions cache
                self.functions = {
                    func["uid"]: func for func in self.ui_config.get("functions", [])
                }
                
                _LOGGER.info("Cached %d functions in coordinator", len(self.functions))
            
            # Get current values for all data points using individual polling
            # ALWAYS poll for values to ensure external changes are detected
            _LOGGER.debug("Fetching current values from device using individual datapoint polling...")
            try:
                values = await self.client.get_values()
                _LOGGER.debug("Successfully received %d values from device via polling", len(values) if values else 0)
                
                # Check for changes
                changes_detected = 0
                if hasattr(self, '_last_values') and self._last_values:
                    for uid, new_value in values.items():
                        old_value = self._last_values.get(uid)
                        if old_value != new_value:
                            _LOGGER.info("🔄 VALUE CHANGE DETECTED: %s: '%s' → '%s'", uid, old_value, new_value)
                            changes_detected += 1
                
                if changes_detected == 0:
                    _LOGGER.debug("No value changes detected in this polling cycle")
                else:
                    _LOGGER.info("📊 Total changes detected: %d", changes_detected)
                
                # Cache values for future comparison
                self._last_values = values.copy()
                
            except Exception as poll_error:
                _LOGGER.warning("Failed to poll for values: %s", poll_error)
                # Fall back to cached values if polling fails
                values = getattr(self, '_last_values', {})
                _LOGGER.debug("Using cached values due to polling failure (%d values)", len(values))

            data = {
                "values": values,
                "ui_config": self.ui_config,
                "functions": self.functions,
                "ui_config_uid": self.ui_config_uid,
            }
            
            _LOGGER.debug("Data update completed successfully")
            return data
            
        except Exception as err:
            _LOGGER.error("Unexpected error during data update: %s", err, exc_info=True)
            raise err

async def test_coordinator_polling():
    """Test if the coordinator polling logic works correctly."""
    _LOGGER.info("🚀 Starting Home Assistant Coordinator Polling Test")
    _LOGGER.info("=" * 70)
    
    # Initialize client
    client = GiraX1Client("10.1.1.85", "admin", "admin")
    
    try:
        # Login
        _LOGGER.info("Logging into Gira X1...")
        await client.login()
        _LOGGER.info("✅ Login successful")
        
        # Create mock coordinator
        coordinator = MockCoordinator(client)
        
        # Run several polling cycles
        _LOGGER.info(f"🔄 Starting {UPDATE_INTERVAL_SECONDS}-second polling cycles...")
        _LOGGER.info("This simulates exactly what the Home Assistant coordinator should be doing")
        _LOGGER.info("")
        
        for cycle in range(1, 11):  # 10 cycles
            _LOGGER.info(f"📍 Polling Cycle {cycle} at {datetime.now().strftime('%H:%M:%S')}")
            
            try:
                # Run the coordinator update method
                data = await coordinator._async_update_data()
                
                values = data.get("values", {})
                _LOGGER.info(f"   ✅ Coordinator update successful - received {len(values)} values")
                
                # Log some key values
                key_uids = ["a02u", "a03c"]  # Our test UIDs
                for uid in key_uids:
                    if uid in values:
                        func_name = coordinator.functions.get(uid, {}).get("displayName", f"UID {uid}")
                        _LOGGER.info(f"   📊 {func_name} ({uid}): '{values[uid]}'")
                
            except Exception as e:
                _LOGGER.error(f"   ❌ Coordinator update failed: {e}")
            
            # Wait for next cycle
            if cycle < 10:
                _LOGGER.info(f"   ⏱️  Waiting {UPDATE_INTERVAL_SECONDS} seconds for next cycle...")
                await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
            
            _LOGGER.info("")
        
        _LOGGER.info("✅ Coordinator polling test completed")
        
    except Exception as e:
        _LOGGER.error(f"❌ Test failed: {e}", exc_info=True)
    finally:
        try:
            await client.logout()
            _LOGGER.info("Logged out from Gira X1")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_coordinator_polling())
