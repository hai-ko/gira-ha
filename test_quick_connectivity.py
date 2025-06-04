#!/usr/bin/env python3
"""
Quick callback endpoint test.
"""

import socket
import ssl
import urllib.request
import urllib.error

# Configuration
HOME_ASSISTANT_IP = "10.1.1.242"
HOME_ASSISTANT_PORT = 8123

def test_tcp():
    """Test basic TCP connectivity."""
    print("🔌 Testing TCP connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((HOME_ASSISTANT_IP, HOME_ASSISTANT_PORT))
        sock.close()
        
        if result == 0:
            print("   ✅ TCP connection successful")
            return True
        else:
            print(f"   ❌ TCP connection failed: error code {result}")
            return False
    except Exception as e:
        print(f"   ❌ TCP test error: {e}")
        return False

def test_https():
    """Test HTTPS connection."""
    print("\n🔐 Testing HTTPS connectivity...")
    
    url = f"https://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/"
    
    try:
        # Create SSL context that ignores certificate verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        request = urllib.request.Request(url)
        request.add_header("Authorization", "Bearer test")
        
        with urllib.request.urlopen(request, context=ssl_context, timeout=10) as response:
            print(f"   ✅ HTTPS connection successful: HTTP {response.status}")
            return True
            
    except urllib.error.URLError as e:
        print(f"   ❌ HTTPS connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ HTTPS error: {e}")
        return False

def test_http():
    """Test HTTP connection."""
    print("\n🌐 Testing HTTP connectivity...")
    
    url = f"http://{HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}/api/"
    
    try:
        request = urllib.request.Request(url)
        request.add_header("Authorization", "Bearer test")
        
        with urllib.request.urlopen(request, timeout=10) as response:
            print(f"   ✅ HTTP connection successful: HTTP {response.status}")
            return True
            
    except urllib.error.URLError as e:
        print(f"   ❌ HTTP connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ HTTP error: {e}")
        return False

def main():
    """Run quick connectivity tests."""
    print("🔍 QUICK CALLBACK CONNECTIVITY TEST")
    print("=" * 40)
    print(f"Target: {HOME_ASSISTANT_IP}:{HOME_ASSISTANT_PORT}")
    
    tcp_ok = test_tcp()
    https_ok = test_https()
    http_ok = test_http()
    
    print(f"\n📊 RESULTS:")
    print(f"TCP:    {'✅ PASS' if tcp_ok else '❌ FAIL'}")
    print(f"HTTPS:  {'✅ PASS' if https_ok else '❌ FAIL'}")
    print(f"HTTP:   {'✅ PASS' if http_ok else '❌ FAIL'}")
    
    if not tcp_ok:
        print(f"\n❌ Network connectivity issue")
    elif not https_ok and not http_ok:
        print(f"\n❌ Home Assistant not responding")
    elif not https_ok:
        print(f"\n⚠️ SSL/TLS issue - HTTPS not working")
    else:
        print(f"\n✅ Connectivity working")

if __name__ == "__main__":
    main()
