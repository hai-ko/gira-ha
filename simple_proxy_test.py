#!/usr/bin/env python3
"""
Simple HTTPS Proxy Connectivity Test

Tests basic connectivity to the HTTPS proxy without external dependencies.
"""

import socket
import subprocess
import ssl
import time

def test_dns_resolution():
    """Test DNS resolution for the proxy domain."""
    print("🔍 Testing DNS resolution...")
    
    try:
        ip = socket.gethostbyname("home.hf17-1.de")
        print(f"   ✅ home.hf17-1.de resolves to: {ip}")
        return ip
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return None

def test_tcp_connectivity(host, port=443):
    """Test basic TCP connectivity."""
    print(f"🔗 Testing TCP connectivity to {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ TCP connection successful to {host}:{port}")
            return True
        else:
            print(f"   ❌ TCP connection failed to {host}:{port} (error: {result})")
            return False
            
    except Exception as e:
        print(f"   ❌ TCP test error: {e}")
        return False

def test_ssl_handshake(host, port=443):
    """Test SSL handshake."""
    print(f"🔒 Testing SSL handshake to {host}:{port}...")
    
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"   ✅ SSL handshake successful")
                print(f"   SSL version: {ssock.version()}")
                return True
                
    except Exception as e:
        print(f"   ❌ SSL handshake failed: {e}")
        return False

def test_http_request(host, port=443):
    """Test basic HTTP request."""
    print(f"📡 Testing HTTP request to {host}:{port}...")
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Connect and make HTTP request
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                # Send HTTP GET request
                request = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
                ssock.send(request.encode())
                
                # Read response
                response = b""
                while True:
                    try:
                        data = ssock.recv(1024)
                        if not data:
                            break
                        response += data
                        if len(response) > 4096:  # Limit response size
                            break
                    except socket.timeout:
                        break
                
                response_str = response.decode('utf-8', errors='ignore')
                
                # Parse status code
                if response_str.startswith('HTTP/'):
                    status_line = response_str.split('\r\n')[0]
                    status_code = status_line.split()[1] if len(status_line.split()) > 1 else "unknown"
                    print(f"   ✅ HTTP response received: {status_code}")
                    print(f"   Response preview: {response_str[:200]}...")
                    return True
                else:
                    print(f"   ❌ Invalid HTTP response")
                    return False
                    
    except Exception as e:
        print(f"   ❌ HTTP request failed: {e}")
        return False

def test_callback_endpoint(host, endpoint):
    """Test specific callback endpoint."""
    print(f"📋 Testing callback endpoint: {endpoint}")
    
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((host, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                # Send HTTP GET request to specific endpoint
                request = f"GET {endpoint} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
                ssock.send(request.encode())
                
                # Read response
                response = b""
                while True:
                    try:
                        data = ssock.recv(1024)
                        if not data:
                            break
                        response += data
                        if len(response) > 2048:
                            break
                    except socket.timeout:
                        break
                
                response_str = response.decode('utf-8', errors='ignore')
                
                if response_str.startswith('HTTP/'):
                    status_line = response_str.split('\r\n')[0]
                    status_code = status_line.split()[1] if len(status_line.split()) > 1 else "unknown"
                    print(f"   Response: HTTP {status_code}")
                    
                    # Analyze response
                    if status_code in ['404', '401', '403']:
                        print(f"   ✅ Proxy forwarding (expected auth/routing response)")
                    elif status_code == '200':
                        print(f"   ✅ Endpoint accessible")
                    elif status_code.startswith('5'):
                        print(f"   ⚠️  Server error - proxy may be misconfigured")
                    else:
                        print(f"   ⚠️  Unexpected response")
                        
                    return True
                else:
                    print(f"   ❌ Invalid response")
                    return False
                    
    except Exception as e:
        print(f"   ❌ Endpoint test failed: {e}")
        return False

def test_network_routing():
    """Test network routing and external connectivity."""
    print("🌐 Testing network routing...")
    
    # Test ping to external service
    try:
        result = subprocess.run(
            ["ping", "-c", "2", "-W", "3", "8.8.8.8"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("   ✅ External internet connectivity working")
        else:
            print("   ❌ External internet connectivity issues")
            print(f"   Ping output: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Network routing test error: {e}")

def main():
    """Main diagnostic function."""
    print("🔧 HTTPS Proxy Connectivity Diagnostic")
    print("=======================================")
    print()
    print("Testing connectivity to: https://home.hf17-1.de")
    print("Expected behavior: Proxy should forward to Home Assistant")
    print()
    
    # Test DNS resolution
    ip = test_dns_resolution()
    print()
    
    if ip:
        # Test TCP connectivity
        tcp_ok = test_tcp_connectivity(ip)
        print()
        
        if tcp_ok:
            # Test SSL handshake
            ssl_ok = test_ssl_handshake(ip)
            print()
            
            if ssl_ok:
                # Test HTTP request
                http_ok = test_http_request("home.hf17-1.de")
                print()
                
                if http_ok:
                    # Test callback endpoints
                    print("Testing callback endpoints:")
                    test_callback_endpoint("home.hf17-1.de", "/api/gira_x1/callback/value")
                    print()
                    test_callback_endpoint("home.hf17-1.de", "/api/gira_x1/callback/service")
                    print()
    
    # Test network routing
    test_network_routing()
    
    print("\n📊 DIAGNOSTIC SUMMARY:")
    print("=" * 50)
    print("✅ If all tests pass: Proxy server is working")
    print("❌ If DNS fails: Domain configuration issue")
    print("❌ If TCP fails: Firewall or routing issue")  
    print("❌ If SSL fails: Certificate or SSL configuration issue")
    print("❌ If HTTP fails: Web server configuration issue")
    print("❌ If endpoints fail: Proxy forwarding misconfiguration")
    print()
    print("🎯 NEXT STEPS:")
    print("1. Check proxy server logs for callback requests")
    print("2. Verify proxy forwards to: https://10.1.1.242:8123")
    print("3. Ensure Gira X1 (10.1.1.85) can reach proxy")
    print("4. Check if proxy requires authentication")

if __name__ == "__main__":
    main()
