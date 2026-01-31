# UDP Integration Checklist

## Pre-Testing Setup

- [ ] Robot is powered on and connected to WiFi
- [ ] Web server can be started: `python g1_app/ui/web_server.py`
- [ ] Robot IP is known (e.g., 192.168.86.3)
- [ ] PC and robot on same WiFi network
- [ ] Port 49504 is not blocked by firewall

## Testing Sequence

### Phase 1: Protocol Module Verification
- [ ] UDP protocol module loads without errors
- [ ] All classes available: UDPProtocolClient, UDPInitializer, UDPActionClient
- [ ] CRC32 validation working
- [ ] Packet parser functional

### Phase 2: Web Server Integration
- [ ] Web server starts successfully
- [ ] New endpoints available:
  - [ ] POST /api/udp/initialize
  - [ ] GET /api/udp/actions
  - [ ] POST /api/udp/play_action
- [ ] API responses are valid JSON
- [ ] Error handling works

### Phase 3: Robot Connection
- [ ] Robot appears in discovery list
- [ ] "Connect" button works in web UI
- [ ] Connection shows robot IP
- [ ] Status shows "Connected"

### Phase 4: UDP Initialization
- [ ] POST /api/udp/initialize returns success
- [ ] No errors in server logs
- [ ] Timestamp shows successful execution

### Phase 5: Action Query
- [ ] GET /api/udp/actions returns list
- [ ] Actions have names and indices
- [ ] "waist_drum_dance" appears in list
- [ ] Response includes action count

### Phase 6: Manual Mode Transition (Critical)
- [ ] Click "Stand Up" button in web UI
- [ ] Robot stands on feet
- [ ] Click "RUN Mode" button
- [ ] FSM state shows "RUN" (500)
- [ ] Robot is in motion-ready state

### Phase 7: Action Playback
- [ ] POST /api/udp/play_action with waist_drum_dance
- [ ] Robot starts executing motion
- [ ] Waist/torso performs drum-like motion
- [ ] Motion completes normally
- [ ] No error messages

### Phase 8: Stop Action
- [ ] Robot stops current motion
- [ ] No lingering commands
- [ ] Robot returns to standing

### Phase 9: Real-Time Updates
- [ ] Open browser DevTools (F12)
- [ ] Go to Console tab
- [ ] Observe WebSocket messages:
  - [ ] udp_initialized event
  - [ ] actions_updated event
  - [ ] action_playing event
  - [ ] action_stopped event

### Phase 10: Error Handling
- [ ] Try playing non-existent action
- [ ] Try playing action in ZERO_TORQUE mode
- [ ] Try with disconnected robot
- [ ] Verify proper error messages returned

## Success Criteria

✅ **All of the following must pass:**

1. UDP module loads without import errors
2. All 4 web API endpoints available
3. Robot can be connected in web UI
4. UDP initialization completes successfully
5. Action list query returns valid data
6. "waist_drum_dance" found in action list
7. Robot transitions to RUN mode via UI
8. Action playback executes on robot
9. Robot performs waist drum motion
10. Stop command halts action
11. WebSocket events broadcast correctly
12. Error cases handled gracefully

## Performance Baselines

Record these times for comparison:

- **Initialization**: _______ ms (target: ~400ms)
- **Query**: _______ ms (target: ~1-3s)
- **Playback response**: _______ ms (target: immediate)
- **Action duration**: _______ seconds

## Issue Tracking

### Issue 1
- **Symptoms**: _______________
- **When occurs**: _______________
- **Attempted fix**: _______________
- **Result**: _______________

### Issue 2
- **Symptoms**: _______________
- **When occurs**: _______________
- **Attempted fix**: _______________
- **Result**: _______________

## Test Log

```
Date: _______________
Tester: _______________
Robot: G1_6937
IP: 192.168.86.3

Results:
- UDP Init: _______________
- Query Actions: _______________
- Playback: _______________
- Stop: _______________
- Overall: PASS / FAIL

Notes:
_________________________________
_________________________________
_________________________________
```

## Sign-Off

- [ ] All tests passed
- [ ] No blocking issues
- [ ] Ready for production use
- [ ] Documentation reviewed

**Tested by**: ________________
**Date**: ________________
**Time**: ________________

---

## Rollback Plan

If issues occur, revert changes:

```bash
# 1. Stop web server
# 2. Backup current files
cp g1_app/ui/web_server.py g1_app/ui/web_server.py.backup
cp g1_app/core/udp_protocol.py g1_app/core/udp_protocol.py.backup

# 3. Restore from git (if needed)
git restore g1_app/ui/web_server.py

# 4. Restart web server
python g1_app/ui/web_server.py
```

## Contact for Issues

If problems occur during testing:

1. Check error messages in web server console
2. Review logs: `web_server.log`
3. Check robot connectivity: `ping <robot_ip>`
4. Verify port: `netstat -an | grep 49504`
5. Review UDP_INTEGRATION_GUIDE.md troubleshooting section

---

**Status**: Ready for Phase 1 testing
