
# 🚀 GIRA X1 INTEGRATION DEPLOYMENT CHECKLIST

## Pre-Deployment Requirements
- [ ] Home Assistant instance with HTTPS configured
- [ ] Network connectivity to Gira X1 device (10.1.1.85)
- [ ] Valid Gira X1 API token
- [ ] Home Assistant accessible on local network

## Deployment Steps
1. [ ] Copy integration files to Home Assistant
   ```
   custom_components/gira_x1/
   ```

2. [ ] Restart Home Assistant

3. [ ] Add Gira X1 integration via UI
   - Host: 10.1.1.85
   - Port: 443 (or 80)
   - Token: [your-api-token]

4. [ ] Check logs for callback registration
   - Look for: "Callbacks enabled" or "using fast polling"
   - No errors about HTTPS or network connectivity

5. [ ] Verify entity creation
   - Lights, switches, covers should appear
   - Entities should respond to commands

6. [ ] Test real-time updates
   - Change device state physically
   - Verify Home Assistant reflects changes quickly

## Troubleshooting
- If callbacks fail: Check HTTPS accessibility from Gira X1
- If polling is slow: Verify fast polling (5s) is active
- If no entities: Check API token and network connectivity

## Success Indicators
✅ "Callbacks enabled" in logs
✅ Real-time updates working
✅ All entities discovered and controllable
✅ No recurring errors in logs
