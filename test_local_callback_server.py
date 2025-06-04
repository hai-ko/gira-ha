#!/usr/bin/env python3
"""
Local callback test server to debug Gira X1 callback test failures.
This will help us understand exactly what the Gira X1 device sends during callback testing.
"""

import asyncio
import json
import logging
from aiohttp import web, ClientSession, TCPConnector
import ssl

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Gira X1 settings
GIRA_HOST = "10.1.1.85"
GIRA_TOKEN = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"
LOCAL_HOST = "0.0.0.0"
LOCAL_PORT = 8080

# Global storage for received requests
received_requests = []

async def value_callback_handler(request):
    """Handle value callback requests."""
    client_ip = request.remote
    method = request.method
    headers = dict(request.headers)
    
    logger.info(f"Value callback - {method} from {client_ip}")
    logger.info(f"Headers: {headers}")
    
    try:
        if request.content_type == 'application/json':
            data = await request.json()
            logger.info(f"JSON Data: {json.dumps(data, indent=2)}")
        else:
            body = await request.text()
            logger.info(f"Body: {body}")
            data = body
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
        data = None
    
    # Store the request for analysis
    request_info = {
        'endpoint': 'value',
        'method': method,
        'client_ip': client_ip,
        'headers': headers,
        'data': data,
        'content_type': request.content_type
    }
    received_requests.append(request_info)
    
    logger.info("Responding with 200 OK")
    return web.Response(status=200, text="OK")

async def service_callback_handler(request):
    """Handle service callback requests."""
    client_ip = request.remote
    method = request.method
    headers = dict(request.headers)
    
    logger.info(f"Service callback - {method} from {client_ip}")
    logger.info(f"Headers: {headers}")
    
    try:
        if request.content_type == 'application/json':
            data = await request.json()
            logger.info(f"JSON Data: {json.dumps(data, indent=2)}")
        else:
            body = await request.text()
            logger.info(f"Body: {body}")
            data = body
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
        data = None
    
    # Store the request for analysis
    request_info = {
        'endpoint': 'service',
        'method': method,
        'client_ip': client_ip,
        'headers': headers,
        'data': data,
        'content_type': request.content_type
    }
    received_requests.append(request_info)
    
    logger.info("Responding with 200 OK")
    return web.Response(status=200, text="OK")

async def register_callbacks_with_gira():
    """Register callbacks with the Gira X1 device."""
    value_callback_url = f"http://{LOCAL_HOST}:{LOCAL_PORT}/api/gira_x1/callback/value"
    service_callback_url = f"http://{LOCAL_HOST}:{LOCAL_PORT}/api/gira_x1/callback/service"
    
    # Note: Using HTTP instead of HTTPS for local testing
    # In production, Gira X1 requires HTTPS
    
    callback_data = {
        "valueCallback": value_callback_url,
        "serviceCallback": service_callback_url,
        "testCallbacks": True
    }
    
    logger.info(f"Registering callbacks with Gira X1 at {GIRA_HOST}")
    logger.info(f"Value callback URL: {value_callback_url}")
    logger.info(f"Service callback URL: {service_callback_url}")
    
    # Create SSL context that ignores certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = TCPConnector(ssl=ssl_context)
    
    async with ClientSession(connector=connector) as session:
        url = f"https://{GIRA_HOST}/api/v2/clients/{GIRA_TOKEN}/callbacks"
        headers = {"Content-Type": "application/json"}
        
        try:
            async with session.post(url, json=callback_data, headers=headers) as response:
                response_text = await response.text()
                logger.info(f"Gira X1 response: {response.status} - {response_text}")
                
                if response.status == 200:
                    logger.info("✅ Callbacks registered successfully!")
                    return True
                else:
                    logger.error(f"❌ Failed to register callbacks: {response.status} - {response_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error registering callbacks: {e}")
            return False

async def unregister_callbacks_with_gira():
    """Unregister callbacks from the Gira X1 device."""
    logger.info("Unregistering callbacks from Gira X1")
    
    # Create SSL context that ignores certificate verification
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = TCPConnector(ssl=ssl_context)
    
    async with ClientSession(connector=connector) as session:
        url = f"https://{GIRA_HOST}/api/v2/clients/{GIRA_TOKEN}/callbacks"
        
        try:
            async with session.delete(url) as response:
                response_text = await response.text()
                logger.info(f"Unregister response: {response.status} - {response_text}")
        except Exception as e:
            logger.error(f"Error unregistering callbacks: {e}")

async def analyze_requests():
    """Analyze the received requests."""
    print("\n" + "="*60)
    print("CALLBACK REQUEST ANALYSIS")
    print("="*60)
    
    if not received_requests:
        print("❌ No requests received!")
        return
    
    for i, req in enumerate(received_requests, 1):
        print(f"\n--- Request {i} ---")
        print(f"Endpoint: {req['endpoint']}")
        print(f"Method: {req['method']}")
        print(f"Client IP: {req['client_ip']}")
        print(f"Content-Type: {req['content_type']}")
        print(f"Headers: {json.dumps(req['headers'], indent=2)}")
        print(f"Data: {json.dumps(req['data'], indent=2) if isinstance(req['data'], dict) else req['data']}")
        
        # Check if this looks like a test request
        if isinstance(req['data'], dict):
            events = req['data'].get('events', [])
            is_test = any(event.get('event') == 'test' for event in events)
            print(f"Is test event: {is_test}")

async def main():
    """Main function to run the test server."""
    print("🧪 Gira X1 Callback Test Server")
    print("="*40)
    print(f"Local server: http://{LOCAL_HOST}:{LOCAL_PORT}")
    print(f"Gira X1 host: {GIRA_HOST}")
    print(f"Token: {GIRA_TOKEN}")
    print()
    
    # Create web application
    app = web.Application()
    app.router.add_route('*', '/api/gira_x1/callback/value', value_callback_handler)
    app.router.add_route('*', '/api/gira_x1/callback/service', service_callback_handler)
    
    # Start the server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, LOCAL_HOST, LOCAL_PORT)
    await site.start()
    
    print(f"✅ Test server started on http://{LOCAL_HOST}:{LOCAL_PORT}")
    print("📞 Registering callbacks with Gira X1...")
    
    try:
        # Register callbacks and wait for test requests
        success = await register_callbacks_with_gira()
        
        if success:
            print("⏳ Waiting 10 seconds for callback tests...")
            await asyncio.sleep(10)
        else:
            print("❌ Registration failed, but waiting anyway to see if any requests come in...")
            await asyncio.sleep(5)
        
        # Analyze what we received
        await analyze_requests()
        
        # Clean up
        await unregister_callbacks_with_gira()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        await runner.cleanup()
        print("🔚 Test server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
