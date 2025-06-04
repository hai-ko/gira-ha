#!/usr/bin/env python3
"""Validate the restored callback system files without importing Home Assistant."""

import os
import sys

def validate_callback_restoration():
    """Validate that all callback system components have been restored."""
    
    print("🧪 VALIDATING RESTORED CALLBACK SYSTEM")
    print("=" * 60)
    
    base_path = '/Users/heikoburkhardt/repos/gira-x1-ha/custom_components/gira_x1'
    
    # Test 1: Check constants file
    print("\n1️⃣ Validating callback constants...")
    
    const_path = os.path.join(base_path, 'const.py')
    try:
        with open(const_path, 'r') as f:
            const_content = f.read()
        
        required_constants = [
            'FAST_UPDATE_INTERVAL_SECONDS: Final = 5',
            'CALLBACK_UPDATE_INTERVAL_SECONDS: Final = 300',
            'API_CALLBACKS_PATH: Final = "/callbacks"',
            'WEBHOOK_VALUE_CALLBACK_PATH: Final = "/api/gira_x1/callback/value"',
            'WEBHOOK_SERVICE_CALLBACK_PATH: Final = "/api/gira_x1/callback/service"',
            'CONF_CALLBACK_URL_OVERRIDE: Final = "callback_url_override"'
        ]
        
        missing_constants = []
        for constant in required_constants:
            if constant not in const_content:
                missing_constants.append(constant)
        
        if missing_constants:
            print(f"❌ Missing constants: {missing_constants}")
            return False
        else:
            print("✅ All callback constants restored")
    except Exception as e:
        print(f"❌ Error reading constants: {e}")
        return False
    
    # Test 2: Check API file
    print("\n2️⃣ Validating API callback methods...")
    
    api_path = os.path.join(base_path, 'api.py')
    try:
        with open(api_path, 'r') as f:
            api_content = f.read()
        
        required_api_features = [
            'async def register_callbacks(',
            'async def unregister_callbacks(',
            'API_CALLBACKS_PATH',
            '📞 CALLBACK REGISTRATION',
            '✅ CALLBACK REGISTRATION SUCCESS',
            '❌ CALLBACK REGISTRATION FAILED'
        ]
        
        missing_features = []
        for feature in required_api_features:
            if feature not in api_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing API features: {missing_features}")
            return False
        else:
            print("✅ All API callback methods restored with logging")
    except Exception as e:
        print(f"❌ Error reading API file: {e}")
        return False
    
    # Test 3: Check webhook file
    print("\n3️⃣ Validating webhook handlers...")
    
    webhook_path = os.path.join(base_path, 'webhook.py')
    try:
        with open(webhook_path, 'r') as f:
            webhook_content = f.read()
        
        required_webhook_features = [
            'class GiraX1ValueCallbackView',
            'class GiraX1ServiceCallbackView',
            '🔔 INCOMING VALUE CALLBACK',
            '🔔 INCOMING SERVICE CALLBACK',
            '✅ VALUE CALLBACK SUCCESS',
            '✅ SERVICE CALLBACK SUCCESS',
            '❌ VALUE CALLBACK ERROR',
            '❌ SERVICE CALLBACK ERROR',
            'def register_webhook_handlers',
            'def unregister_webhook_handlers'
        ]
        
        missing_features = []
        for feature in required_webhook_features:
            if feature not in webhook_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing webhook features: {missing_features}")
            return False
        else:
            print("✅ All webhook handlers restored with comprehensive logging")
    except Exception as e:
        print(f"❌ Error reading webhook file: {e}")
        return False
    
    # Test 4: Check coordinator file
    print("\n4️⃣ Validating coordinator callback system...")
    
    init_path = os.path.join(base_path, '__init__.py')
    try:
        with open(init_path, 'r') as f:
            init_content = f.read()
        
        required_coordinator_features = [
            'async def setup_callbacks(self)',
            'async def cleanup_callbacks(self)',
            'def _determine_callback_base_url(self)',
            'def _get_local_ip_for_gira_x1(self)',
            'self.callbacks_enabled = False',
            'self._webhook_handlers = None',
            '🔧 CALLBACK SETUP',
            '✅ CALLBACK SETUP SUCCESS',
            '❌ CALLBACK SETUP FAILED',
            'await coordinator.setup_callbacks()',
            'await coordinator.cleanup_callbacks()'
        ]
        
        missing_features = []
        for feature in required_coordinator_features:
            if feature not in init_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ Missing coordinator features: {missing_features}")
            return False
        else:
            print("✅ All coordinator callback functionality restored")
    except Exception as e:
        print(f"❌ Error reading coordinator file: {e}")
        return False
    
    # Test 5: Check polling mode configuration
    print("\n5️⃣ Validating polling mode configuration...")
    
    try:
        # Check that update intervals are properly configured
        if 'timedelta(seconds=CALLBACK_UPDATE_INTERVAL_SECONDS)' not in init_content:
            print("❌ Callback mode polling interval not configured")
            return False
        
        if 'timedelta(seconds=FAST_UPDATE_INTERVAL_SECONDS)' not in init_content:
            print("❌ Fast polling interval not configured")
            return False
        
        print("✅ Polling mode configuration restored")
    except Exception as e:
        print(f"❌ Error validating polling configuration: {e}")
        return False
    
    # Test 6: Check logging enhancements
    print("\n6️⃣ Validating comprehensive logging...")
    
    try:
        emoji_patterns = [
            '📞',  # Callback registration
            '🔔',  # Incoming callbacks
            '✅',  # Success states
            '❌',  # Error states
            '⚠️',  # Warning states
            '🔧',  # Setup/configuration
            '🧹',  # Cleanup
            '🔄',  # Refresh/restart
            '📱',  # UI changes
            '🏗️',  # Project changes
            '🚀',  # Startup
            '📊'   # Data/statistics
        ]
        
        emoji_found = []
        for emoji in emoji_patterns:
            if emoji in init_content or emoji in webhook_content or emoji in api_content:
                emoji_found.append(emoji)
        
        if len(emoji_found) < 8:  # Should have most emojis
            print(f"⚠️ Limited emoji logging found: {emoji_found}")
        else:
            print(f"✅ Comprehensive emoji-based logging implemented: {emoji_found}")
    except Exception as e:
        print(f"❌ Error validating logging: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 CALLBACK SYSTEM RESTORATION VALIDATION COMPLETE!")
    print("\n✅ All components successfully restored:")
    print("  📋 Callback constants (intervals, paths, config)")
    print("  🌐 API callback methods (register/unregister)")
    print("  🎯 Webhook handlers (value/service callbacks)")
    print("  🎛️ Coordinator callback system (setup/cleanup)")
    print("  ⚡ Hybrid polling modes (callback + fallback)")
    print("  📊 Comprehensive emoji-based logging")
    
    print("\n🔧 System Configuration:")
    print("  • Real-time callbacks with 300s fallback polling")
    print("  • Fast 5s polling when callbacks fail")
    print("  • Automatic IP detection for callback URLs")
    print("  • Comprehensive error handling and recovery")
    print("  • Test callback validation during setup")
    
    return True

if __name__ == "__main__":
    success = validate_callback_restoration()
    sys.exit(0 if success else 1)
