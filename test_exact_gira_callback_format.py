#!/usr/bin/env python3
"""
Test script that simulates EXACTLY what the Gira X1 device sends during callback testing.
Based on the official Gira IoT REST API documentation.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
GIRA_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"
HOME_ASSISTANT_BASE_URL = "https://heiko.duckdns.org:8123"
SERVICE_CALLBACK_URL = f"{HOME_ASSISTANT_BASE_URL}/api/gira_x1/service_callback"
VALUE_CALLBACK_URL = f"{HOME_ASSISTANT_BASE_URL}/api/gira_x1/value_callback"

async def test_service_callback_test_event():
    """Test the service callback endpoint with a test event exactly as Gira X1 sends it."""
    logger.info("Testing service callback with test event...")
    
    # This is the exact format the Gira X1 sends for service callback testing
    test_payload = {
        "token": GIRA_TOKEN,
        "events": [
            {
                "event": "test"
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info(f"Sending test event to {SERVICE_CALLBACK_URL}")
            logger.info(f"Payload: {json.dumps(test_payload, indent=2)}")
            
            async with session.post(
                SERVICE_CALLBACK_URL,
                json=test_payload,
                headers={"Content-Type": "application/json"},
                ssl=False  # For testing with self-signed certs
            ) as response:
                status = response.status
                text = await response.text()
                
                logger.info(f"Service callback test response: {status}")
                logger.info(f"Response text: {text}")
                
                if status == 200:
                    logger.info("✅ Service callback test PASSED")
                else:
                    logger.error(f"❌ Service callback test FAILED - Expected 200, got {status}")
                
                return status == 200
                
        except Exception as e:
            logger.error(f"❌ Service callback test FAILED with exception: {e}")
            return False

async def test_value_callback_test_event():
    """Test the value callback endpoint with a test event."""
    logger.info("Testing value callback with test event...")
    
    # For value callbacks, the test format is less clear in documentation
    # Let's try an empty events array first (as seen in our current detection logic)
    test_payload = {
        "token": GIRA_TOKEN,
        "events": []
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info(f"Sending test event to {VALUE_CALLBACK_URL}")
            logger.info(f"Payload: {json.dumps(test_payload, indent=2)}")
            
            async with session.post(
                VALUE_CALLBACK_URL,
                json=test_payload,
                headers={"Content-Type": "application/json"},
                ssl=False  # For testing with self-signed certs
            ) as response:
                status = response.status
                text = await response.text()
                
                logger.info(f"Value callback test response: {status}")
                logger.info(f"Response text: {text}")
                
                if status == 200:
                    logger.info("✅ Value callback test PASSED")
                else:
                    logger.error(f"❌ Value callback test FAILED - Expected 200, got {status}")
                
                return status == 200
                
        except Exception as e:
            logger.error(f"❌ Value callback test FAILED with exception: {e}")
            return False

async def test_value_callback_with_test_event():
    """Test value callback with explicit test event (alternative format)."""
    logger.info("Testing value callback with explicit test event...")
    
    # Alternative test format - similar to service callback
    test_payload = {
        "token": GIRA_TOKEN,
        "events": [
            {
                "event": "test"
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            logger.info(f"Sending alternative test event to {VALUE_CALLBACK_URL}")
            logger.info(f"Payload: {json.dumps(test_payload, indent=2)}")
            
            async with session.post(
                VALUE_CALLBACK_URL,
                json=test_payload,
                headers={"Content-Type": "application/json"},
                ssl=False
            ) as response:
                status = response.status
                text = await response.text()
                
                logger.info(f"Value callback alternative test response: {status}")
                logger.info(f"Response text: {text}")
                
                return status == 200
                
        except Exception as e:
            logger.error(f"❌ Value callback alternative test FAILED with exception: {e}")
            return False

async def test_get_requests():
    """Test GET requests to both endpoints (some devices test endpoint availability this way)."""
    logger.info("Testing GET requests to callback endpoints...")
    
    endpoints = [
        ("Service Callback", SERVICE_CALLBACK_URL),
        ("Value Callback", VALUE_CALLBACK_URL)
    ]
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for name, url in endpoints:
            try:
                logger.info(f"Sending GET request to {name}: {url}")
                
                async with session.get(url, ssl=False) as response:
                    status = response.status
                    text = await response.text()
                    
                    logger.info(f"{name} GET response: {status}")
                    logger.info(f"Response text: {text}")
                    
                    if status == 200:
                        logger.info(f"✅ {name} GET test PASSED")
                        results.append(True)
                    else:
                        logger.error(f"❌ {name} GET test FAILED - Expected 200, got {status}")
                        results.append(False)
                        
            except Exception as e:
                logger.error(f"❌ {name} GET test FAILED with exception: {e}")
                results.append(False)
    
    return all(results)

async def test_connectivity():
    """Test basic connectivity to Home Assistant."""
    logger.info("Testing basic connectivity to Home Assistant...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test basic Home Assistant connectivity
            async with session.get(f"{HOME_ASSISTANT_BASE_URL}/", ssl=False) as response:
                logger.info(f"Home Assistant connectivity test: {response.status}")
                return response.status in [200, 401, 403]  # Any of these means we can reach HA
                
        except Exception as e:
            logger.error(f"❌ Connectivity test FAILED: {e}")
            return False

async def simulate_normal_events():
    """Test that normal events are still processed correctly."""
    logger.info("Testing normal event processing...")
    
    # Test normal service event
    service_event = {
        "token": GIRA_TOKEN,
        "events": [
            {
                "event": "startup"
            }
        ]
    }
    
    # Test normal value event
    value_event = {
        "token": GIRA_TOKEN,
        "events": [
            {
                "uid": "12345",
                "value": "test_value"
            }
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        results = []
        
        # Test service event
        try:
            async with session.post(SERVICE_CALLBACK_URL, json=service_event, ssl=False) as response:
                logger.info(f"Normal service event response: {response.status}")
                results.append(response.status == 200)
        except Exception as e:
            logger.error(f"Normal service event failed: {e}")
            results.append(False)
        
        # Test value event
        try:
            async with session.post(VALUE_CALLBACK_URL, json=value_event, ssl=False) as response:
                logger.info(f"Normal value event response: {response.status}")
                results.append(response.status == 200)
        except Exception as e:
            logger.error(f"Normal value event failed: {e}")
            results.append(False)
        
        return all(results)

async def main():
    """Run all callback tests."""
    logger.info("=" * 60)
    logger.info("GIRA X1 CALLBACK TEST SIMULATION")
    logger.info("=" * 60)
    logger.info(f"Target Home Assistant: {HOME_ASSISTANT_BASE_URL}")
    logger.info(f"Using token: {GIRA_TOKEN}")
    logger.info("=" * 60)
    
    tests = [
        ("Connectivity", test_connectivity()),
        ("GET Requests", test_get_requests()),
        ("Service Callback Test Event", test_service_callback_test_event()),
        ("Value Callback Test Event (Empty)", test_value_callback_test_event()),
        ("Value Callback Test Event (Explicit)", test_value_callback_with_test_event()),
        ("Normal Events", simulate_normal_events()),
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            result = await test_coro
            results.append((test_name, result))
            logger.info(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
        except Exception as e:
            logger.error(f"{test_name}: ❌ FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 ALL TESTS PASSED - Callback implementation should work with Gira X1!")
    else:
        logger.error("❌ Some tests failed - there may be connectivity or implementation issues")

if __name__ == "__main__":
    asyncio.run(main())
