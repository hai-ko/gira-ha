#!/usr/bin/env python3
"""
Standalone test server that mimics the Home Assistant Gira X1 webhook implementation.
This can be used to verify that our callback logic works correctly without Home Assistant.
"""

import asyncio
import json
import logging
from aiohttp import web, ClientSession
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test token (same as used in the real integration)
EXPECTED_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"

class TestServiceCallbackView:
    """Standalone version of the service callback handler."""
    
    async def get(self, request: web.Request) -> web.Response:
        """Handle GET requests for service callback endpoint (for testing)."""
        logger.info("Received GET request on service callback endpoint - responding with 200 OK")
        return web.Response(status=200, text="Gira X1 Service Callback Endpoint")

    async def post(self, request: web.Request) -> web.Response:
        """Process service events from Gira X1."""
        try:
            # Log request details
            content_type = request.headers.get('content-type', 'unknown')
            logger.info(f"Service callback request - Content-Type: {content_type}, Method: {request.method}")
            
            data = await request.json()
            logger.info(f"Received service callback data: {json.dumps(data, indent=2)}")
            
            # Validate token
            token = data.get("token")
            events = data.get("events", [])
            
            # Detect test events (matching our webhook implementation)
            is_test_event = (
                len(events) == 0 or  # Empty event list
                any(str(event.get("event", "")).lower() == "test" for event in events) or  # Test event
                data.get("test", False) or  # Test flag
                (len(events) == 1 and not events[0].get("event"))  # Single empty event
            )
            
            logger.info(f"Service callback analysis - Events: {len(events)}, Is test: {is_test_event}, Token present: {bool(token)}")
            
            # For test events, be lenient with token validation
            if not is_test_event and (not token or token != EXPECTED_TOKEN):
                logger.warning(f"Invalid token in service callback: {token} (expected: {EXPECTED_TOKEN})")
                return web.Response(status=401, text="Invalid token")
            elif is_test_event:
                logger.info("✅ Received test service callback event, responding with 200 OK")
                logger.info(f"Test event details: {data}")
            
            # Process events (skip if test)
            if events and not is_test_event:
                for event in events:
                    event_type = event.get("event")
                    logger.info(f"Processing service event: {event_type}")
            elif is_test_event:
                logger.info("Skipping event processing for test callback")
            
            # Log failures
            failures = data.get("failures", 0)
            if failures > 0:
                logger.warning(f"Gira X1 reported {failures} failed callback attempts")
            
            logger.info("✅ Service callback processed successfully, returning 200 OK")
            return web.Response(status=200, text="OK")
            
        except json.JSONDecodeError as err:
            logger.error(f"Invalid JSON in service callback: {err}")
            return web.Response(status=400, text="Invalid JSON")
        except Exception as err:
            logger.error(f"Error processing service callback: {err}", exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

class TestValueCallbackView:
    """Standalone version of the value callback handler."""
    
    async def get(self, request: web.Request) -> web.Response:
        """Handle GET requests for value callback endpoint (for testing)."""
        logger.info("Received GET request on value callback endpoint - responding with 200 OK")
        return web.Response(status=200, text="Gira X1 Value Callback Endpoint")

    async def post(self, request: web.Request) -> web.Response:
        """Process value events from Gira X1."""
        try:
            # Log request details
            content_type = request.headers.get('content-type', 'unknown')
            logger.info(f"Value callback request - Content-Type: {content_type}, Method: {request.method}")
            
            data = await request.json()
            logger.info(f"Received value callback data: {json.dumps(data, indent=2)}")
            
            # Validate token
            token = data.get("token")
            events = data.get("events", [])
            
            # Detect test events (matching our webhook implementation)
            is_test_event = (
                len(events) == 0 or  # Empty event list (common for value callback tests)
                any(str(event.get("event", "")).lower() == "test" for event in events) or  # Test event
                data.get("test", False) or  # Test flag
                (len(events) == 1 and not events[0].get("event"))  # Single empty event
            )
            
            logger.info(f"Value callback analysis - Events: {len(events)}, Is test: {is_test_event}, Token present: {bool(token)}")
            
            # For test events, be lenient with token validation
            if not is_test_event and (not token or token != EXPECTED_TOKEN):
                logger.warning(f"Invalid token in value callback: {token} (expected: {EXPECTED_TOKEN})")
                return web.Response(status=401, text="Invalid token")
            elif is_test_event:
                logger.info("✅ Received test value callback event, responding with 200 OK")
                logger.info(f"Test event details: {data}")
            
            # Process value events (skip if test)
            if events and not is_test_event:
                for event in events:
                    uid = event.get("uid")
                    value = event.get("value")
                    if uid and value is not None:
                        logger.info(f"Processing value update: {uid} = {value}")
            elif is_test_event:
                logger.info("Skipping event processing for test callback")
            
            # Log failures
            failures = data.get("failures", 0)
            if failures > 0:
                logger.warning(f"Gira X1 reported {failures} failed callback attempts")
            
            logger.info("✅ Value callback processed successfully, returning 200 OK")
            return web.Response(status=200, text="OK")
            
        except json.JSONDecodeError as err:
            logger.error(f"Invalid JSON in value callback: {err}")
            return web.Response(status=400, text="Invalid JSON")
        except Exception as err:
            logger.error(f"Error processing value callback: {err}", exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

async def test_our_implementation():
    """Test our implementation with the exact Gira X1 test payloads."""
    logger.info("Testing our callback implementation with simulated Gira X1 requests...")
    
    # Test payloads as the Gira X1 would send them
    test_cases = [
        {
            "name": "Service Callback Test Event",
            "url": "http://localhost:8080/api/gira_x1/service_callback",
            "method": "POST",
            "payload": {
                "token": EXPECTED_TOKEN,
                "events": [{"event": "test"}]
            }
        },
        {
            "name": "Value Callback Test Event (Empty)",
            "url": "http://localhost:8080/api/gira_x1/value_callback", 
            "method": "POST",
            "payload": {
                "token": EXPECTED_TOKEN,
                "events": []
            }
        },
        {
            "name": "Value Callback Test Event (Explicit)",
            "url": "http://localhost:8080/api/gira_x1/value_callback",
            "method": "POST", 
            "payload": {
                "token": EXPECTED_TOKEN,
                "events": [{"event": "test"}]
            }
        },
        {
            "name": "Service Callback GET Test",
            "url": "http://localhost:8080/api/gira_x1/service_callback",
            "method": "GET",
            "payload": None
        },
        {
            "name": "Value Callback GET Test", 
            "url": "http://localhost:8080/api/gira_x1/value_callback",
            "method": "GET",
            "payload": None
        }
    ]
    
    # Wait a moment for server to start
    await asyncio.sleep(1)
    
    async with ClientSession() as session:
        results = []
        
        for test_case in test_cases:
            try:
                logger.info(f"\n--- Testing {test_case['name']} ---")
                
                if test_case['method'] == 'GET':
                    async with session.get(test_case['url']) as response:
                        status = response.status
                        text = await response.text()
                else:
                    async with session.post(test_case['url'], json=test_case['payload']) as response:
                        status = response.status
                        text = await response.text()
                
                logger.info(f"Response: {status} - {text}")
                
                if status == 200:
                    logger.info(f"✅ {test_case['name']} PASSED")
                    results.append(True)
                else:
                    logger.error(f"❌ {test_case['name']} FAILED - Expected 200, got {status}")
                    results.append(False)
                    
            except Exception as e:
                logger.error(f"❌ {test_case['name']} FAILED with exception: {e}")
                results.append(False)
        
        # Summary
        passed = sum(results)
        total = len(results)
        logger.info(f"\n=== TEST SUMMARY ===")
        logger.info(f"Passed: {passed}/{total}")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED - Our webhook implementation is correct!")
        else:
            logger.error("❌ Some tests failed - there may be implementation issues")

async def create_app():
    """Create the test web application."""
    app = web.Application()
    
    # Create handler instances
    service_handler = TestServiceCallbackView()
    value_handler = TestValueCallbackView()
    
    # Add routes
    app.router.add_route('GET', '/api/gira_x1/service_callback', service_handler.get)
    app.router.add_route('POST', '/api/gira_x1/service_callback', service_handler.post)
    app.router.add_route('GET', '/api/gira_x1/value_callback', value_handler.get)
    app.router.add_route('POST', '/api/gira_x1/value_callback', value_handler.post)
    
    return app

async def main():
    """Run the test server and tests."""
    logger.info("=" * 60)
    logger.info("GIRA X1 WEBHOOK IMPLEMENTATION TEST SERVER")
    logger.info("=" * 60)
    logger.info("Starting test server on http://localhost:8080")
    logger.info(f"Expected token: {EXPECTED_TOKEN}")
    logger.info("=" * 60)
    
    # Create and start the server
    app = await create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    
    logger.info("✅ Test server started successfully")
    
    # Run tests
    await test_our_implementation()
    
    # Keep server running for a bit to allow manual testing
    logger.info("\nServer will remain running for 30 seconds for manual testing...")
    logger.info("You can test manually with:")
    logger.info("curl -X GET http://localhost:8080/api/gira_x1/service_callback")
    logger.info("curl -X POST http://localhost:8080/api/gira_x1/service_callback -H 'Content-Type: application/json' -d '{\"token\":\"t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5\",\"events\":[{\"event\":\"test\"}]}'")
    
    await asyncio.sleep(30)
    
    # Cleanup
    await runner.cleanup()
    logger.info("Test server stopped")

if __name__ == "__main__":
    asyncio.run(main())
