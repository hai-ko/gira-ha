#!/usr/bin/env python3
"""
Simple webhook test to understand exactly what's failing with Gira X1 callbacks.
"""

# Looking at the Gira documentation and error message, let's analyze the issue:
# 
# Error: "Callback test failed for serviceCallback."
# This means the Gira X1 device tried to POST to our service callback URL during
# the testCallbacks=true phase, but didn't receive a proper 200 OK response.

# From the documentation:
# 1. When testCallbacks=true, the Gira X1 sends a test event
# 2. Test events have: {"event": "test"} in the events array  
# 3. The callback server MUST respond with 200 OK
# 4. If any other response is received, the test fails

# Let's check our current webhook implementation...

def analyze_webhook_implementation():
    """Analyze the current webhook implementation for callback test handling."""
    
    print("🔍 Analyzing Webhook Implementation for Callback Test Issues")
    print("=" * 60)
    
    # Check the current webhook paths
    webhook_paths = {
        "value_callback": "/api/gira_x1/callback/value",
        "service_callback": "/api/gira_x1/callback/service"
    }
    
    print("📍 Configured Webhook Paths:")
    for name, path in webhook_paths.items():
        print(f"  {name}: {path}")
    
    print("\n🔧 Callback Test Requirements (from Gira docs):")
    print("  1. Gira X1 sends POST request to callback URL")
    print("  2. Request includes test event: {'event': 'test'}")
    print("  3. Server MUST respond with HTTP 200 OK")
    print("  4. Any other response = test failure")
    
    print("\n📋 Current Test Detection Logic:")
    print("  - Empty events array: ✅ Detected as test")
    print("  - Explicit 'test' event: ✅ Detected as test (case-insensitive)")
    print("  - Test flag in data: ✅ Detected as test")
    print("  - Single empty event: ✅ Detected as test")
    
    print("\n⚠️  Potential Issues:")
    issues = [
        "HTTPS requirement: Gira X1 requires HTTPS for callbacks",
        "Network accessibility: Gira X1 must be able to reach HA instance", 
        "URL format: Callback URLs must be properly formatted",
        "Response timing: Must respond quickly with 200 OK",
        "Request parsing: Must handle JSON properly without errors"
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    print("\n🎯 Next Steps for Debugging:")
    steps = [
        "Check Home Assistant external URL configuration",
        "Verify Gira X1 can reach Home Assistant over HTTPS",
        "Test webhook endpoints manually",
        "Add more detailed logging to webhook handlers",
        "Verify SSL certificate handling"
    ]
    
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")

def check_network_accessibility():
    """Provide guidance on network accessibility issues."""
    
    print("\n🌐 Network Accessibility Checklist:")
    print("=" * 40)
    
    checks = [
        ("External URL", "Is Home Assistant accessible from Gira X1's network?"),
        ("HTTPS Setup", "Is HTTPS properly configured in Home Assistant?"),
        ("Firewall", "Are the required ports open?"),
        ("DNS Resolution", "Can Gira X1 resolve the HA hostname?"),
        ("SSL Certificate", "Is the SSL certificate valid or properly ignored?"),
    ]
    
    for check, description in checks:
        print(f"  ✓ {check}: {description}")
    
    print("\n📝 Common Issues:")
    print("  - HA running on HTTP but Gira X1 requires HTTPS")
    print("  - Self-signed certificates causing connection failures")
    print("  - Network segmentation preventing Gira X1 -> HA communication")
    print("  - Incorrect external URL configuration in HA")

def suggest_debugging_approach():
    """Suggest a systematic debugging approach."""
    
    print("\n🛠️  Systematic Debugging Approach:")
    print("=" * 40)
    
    print("1. 📍 Verify Home Assistant Configuration:")
    print("   - Check configuration.yaml for external_url")
    print("   - Ensure HTTPS is properly configured")
    print("   - Verify the URL is reachable from Gira X1's network")
    
    print("\n2. 🔍 Test Network Connectivity:")
    print("   - From Gira X1 network, test: curl -k https://<your-ha-url>/api/gira_x1/callback/service")
    print("   - Should return 404 or method not allowed (proves reachability)")
    
    print("\n3. 📊 Enhanced Logging:")
    print("   - Add debug logging to webhook handlers")
    print("   - Monitor Home Assistant logs during callback registration")
    print("   - Check for any incoming requests to webhook endpoints")
    
    print("\n4. 🧪 Manual Testing:")
    print("   - Use curl/postman to test webhook endpoints")
    print("   - Simulate the exact test request Gira X1 sends")
    
    print("\n5. 🔧 Alternative Approaches:")
    print("   - Try callback registration without testing (testCallbacks=false)")
    print("   - Use ngrok or similar to expose HA temporarily")
    print("   - Check if polling mode works as fallback")

def main():
    """Main analysis function."""
    analyze_webhook_implementation()
    check_network_accessibility()
    suggest_debugging_approach()
    
    print("\n" + "=" * 60)
    print("🎯 IMMEDIATE ACTION ITEMS:")
    print("=" * 60)
    print("1. Check Home Assistant external URL configuration")
    print("2. Test HTTPS connectivity from Gira X1 to Home Assistant")
    print("3. Enable debug logging for the gira_x1 integration")
    print("4. Monitor logs during callback registration attempt")
    print("5. Consider temporarily using testCallbacks=false as workaround")
    
    print("\n📞 The callback test is failing because:")
    print("   The Gira X1 device cannot successfully connect to")
    print("   the Home Assistant webhook endpoints to perform the test.")

if __name__ == "__main__":
    main()
