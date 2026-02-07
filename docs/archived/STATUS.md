# G1 Robot Controller - Current Status & Work Log

**Date**: February 5, 2026 | **Updated**: Hybrid discovery implemented  
**Robot**: G1_6937 (192.168.86.18) | **Model**: G1 Air (WebRTC only)  
**Goal**: Reliable robot discovery + Complete SLAM mapping test workflow

---

## 🚀 LATEST: Robot Discovery Fix (Feb 5)

### Problem Solved
- **Issue**: ARP discovery fails daily (robot appears offline even when on network)
- **Root Cause**: Robot has incomplete ARP entry (doesn't respond to ARP requests)
- **Solution**: Hybrid discovery strategy combining cached IPs + ARP fallback

### Implementation
- ✅ **Phase 1**: Try cached IP from ~/.unitree_robot_bindings.json (instant, 99% case)
- ✅ **Phase 2**: ARP scan fallback for IP changes
- ✅ **Persistence**: Save successful IPs to bindings for next session
- ✅ **Bug Fix**: Fixed ARP parser treating interface name as MAC address

### Documentation
- See **[DISCOVERY_HYBRID_FIX.md](DISCOVERY_HYBRID_FIX.md)** for detailed explanation

---

## 📚 DOCUMENTATION

### Primary References (Read These)
1. **[STATUS.md](STATUS.md)** ← You are here (current work status)
2. **[DISCOVERY_HYBRID_FIX.md](DISCOVERY_HYBRID_FIX.md)** ← Latest fix explanation
3. **[G1_WEBRTC_PROTOCOL.md](G1_WEBRTC_PROTOCOL.md)** ← Architecture & protocol guide
4. **[QUICKSTART.md](QUICKSTART.md)** ← How to run tests

### Supporting Documentation
- SDK docs in `unitree_docs/` (pristine, don't touch)
- Test scripts in `g1_tests/` (organized by function)

---

## ✅ COMPLETED

### Discovery System (Feb 5)
- ✅ Diagnosed ARP discovery failure root cause
- ✅ Implemented hybrid strategy (cached IP + ARP fallback)
- ✅ Fixed ARP parser bug (interface name confusion)
- ✅ Added IP persistence to bindings file
- ✅ Added WebRTC connectivity verification
- ✅ Tested all components (working correctly)

### Test Suite Organization (Feb 4)
- ✅ Cleaned up 91 scattered test files
- ✅ Organized into `g1_tests/` with 6 categories
- ✅ Created 14 standardized test scripts
- ✅ `robot_test_helpers.py` as standard connection module

### API Discovery
- ✅ Verified correct API IDs from `g1_app/core/command_executor.py`
- ✅ Found actual working code format (Feb 3 test_slam_save_load.py)
- ✅ **CORRECT FORMAT**: Uses `"api_id"` + `"parameter"` keys, NOT header/identity

### Code Format (VERIFIED WORKING Feb 3)
```python
# Correct format from test_slam_save_load.py
payload = {
    "api_id": 1804,  # API ID
    "parameter": json.dumps({
        "data": { ... }
    })
}
await conn.datachannel.pub_sub.publish_request_new(
    "rt/api/slam_operate/request",
    payload
)
```

### SLAM API IDs
| Operation | API ID | Code | Status |
|-----------|--------|------|--------|
| START_MAPPING | 1801 | slam_start_mapping() | ✅ Working |
| END_MAPPING | 1802 | slam_stop_mapping() | ✅ Working |
| INITIALIZE_POSE | 1804 | slam_load_map() | ✅ Working |
| POSE_NAVIGATION | 1102 | slam_navigate_to() | ✅ Working |
| CLOSE_SLAM | 1901 | slam_close() | ✅ Working |

### Test Script Created
- ✅ `/root/G1/unitree_sdk2/g1_tests/slam/simple_slam_test.py`
- ✅ Uses VERIFIED format from Feb 3 (test_slam_save_load.py)
- ✅ 6-phase workflow: START → SAVE → LOAD → MONITOR → NAVIGATE → CLOSE

---

## 🔄 IN PROGRESS

### SLAM Mapping Workflow Test
- **File**: `g1_tests/slam/simple_slam_test.py`
- **Status**: Ready to run
- **Next**: Execute test with robot ready

**6-Phase Workflow:**
1. START_MAPPING (1801) - User walks robot around room
2. SAVE_MAP (1802) - Stop and save as test_simple.pcd
3. LOAD_MAP (1804) - Load map with initial pose (0,0,0)
4. MONITOR_POSES (15s) - Listen for rt/slam_info updates
5. NAVIGATE (1102) - Test navigation to (0.5, 0.5)
6. CLOSE_SLAM (1901) - Clean shutdown

**Expected Output:**
- Map saved to `/home/unitree/test_simple.pcd`
- Pose updates printed every 5 messages
- Navigation test completes

---

## ⚠️ KNOWN ISSUES

### Issue 1: g1_app Code Is Incorrect
- ❌ `g1_app/core/command_executor.py` uses wrong format (parameter-style with broken structure)
- ✅ Use Feb 3 `test_slam_save_load.py` format instead
- **Impact**: Don't copy code from g1_app for SLAM - use working test patterns

### Issue 2: Old Documentation (RESOLVED)
- ❌ 76 old markdown files cluttering workspace
- ✅ All archived to `_archived_docs/`
- **Now using**: This single STATUS.md for tracking

---

## 📋 TODO - NEXT STEPS

### Immediate (Today Feb 4)
1. **Stop web server** (only one WebRTC client allowed)
   ```bash
   pkill -f "python3 g1_app"
   ```

2. **Run SLAM test**
   ```bash
   cd /root/G1/unitree_sdk2/g1_tests/slam
   python3 simple_slam_test.py
   ```

3. **Expected interactions**:
   - Prompt: "Walk robot around room" → Press Enter when done
   - Observe: Pose updates printed to console
   - Result: "✅ SLAM TEST COMPLETE"

4. **Verify success**:
   - Check map saved: `/home/unitree/test_simple.pcd`
   - Check coordinate changes in output

### If Test Fails
- **Check error message** - script will print exact failure
- **Check connection** - robot must be powered on + WiFi connected
- **Check IP** - update robot_ip in test if needed (currently 192.168.86.18)

---

## 🔧 Key Technical Details

### WebRTC Connection
- Single client only - stop g1_app before running tests
- Use `UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.18")`
- Import: `from unitree_webrtc_connect.webrtc_connection import ...`

### SLAM API Pattern
**Always use this format:**
```python
payload = {
    "api_id": 1802,           # Required: API ID
    "parameter": json.dumps({ # Required: JSON-encoded parameter
        "data": {
            "address": "/home/unitree/map.pcd"  # Actual parameters
        }
    })
}
```

### Map File Paths
- Always use full path: `/home/unitree/{name}.pcd`
- Robot stores locally on PC1
- No HTTP download needed for basic testing

### Pose Coordinates
- `rt/slam_info` publishes pose updates during active mapping
- Format: `{"type": "mapping_info", "data": {"currentPose": {...}}}`
- Fields: `x`, `y`, `z`, `q_x`, `q_y`, `q_z`, `q_w`

---

## 📁 Clean File Organization

```
/root/G1/unitree_sdk2/
├── 📄 STATUS.md                       ← Current work status
├── 📄 G1_WEBRTC_PROTOCOL.md           ← Architecture & protocol guide
├── 📄 robot_test_helpers.py           ← Connection helper module
│
├── 📂 g1_tests/                       ← All test scripts
│   ├── slam/
│   │   ├── simple_slam_test.py       ✅ READY TO RUN
│   │   └── [other slam tests]
│   └── [other test categories]
│
├── 📂 g1_app/                         ← Web controller (pristine SDK)
│   ├── core/
│   │   ├── robot_controller.py       ✅ Working WebRTC
│   │   └── command_executor.py       ⚠️  Some code needs fixes
│   └── ui/web_server.py
│
├── 📂 _scripts/                       ← Utility shell scripts
├── 📂 _analysis/                      ← Research & analysis code
├── 📂 _archived_docs/                 ← Old documentation (76 files)
├── 📂 _old_files/                     ← Legacy logs & captures
│
└── 📂 [SDK directories] (pristine)
    ├── cmake/
    ├── example/
    ├── include/
    ├── lib/
    ├── licenses/
    └── unitree_docs/
```

**Key Points:**
- Only 14 files in root (clean!)
- All test files organized in g1_tests/
- All old documentation archived
- SDK directories remain untouched
- Single source of truth: STATUS.md + G1_WEBRTC_PROTOCOL.md

---

## 🔍 Debug Checklist

If test fails, verify:

- [ ] Robot powered on + green WiFi indicator
- [ ] PC connected to same WiFi network
- [ ] Robot IP reachable: `ping 192.168.86.18`
- [ ] WebRTC connection works: Check status in test output
- [ ] No other processes using robot connection (check `ps aux | grep g1_app`)
- [ ] FSM state correct: Robot should be in RUN mode (fsm_id=801)

---

## 🎯 Success Criteria

Test passes when:
- ✅ "PHASE 1: START MAPPING" → Mapping starts successfully
- ✅ "PHASE 2: SAVE MAP" → Map saved with ✅ indicator
- ✅ "PHASE 3: LOAD MAP" → Map loaded with ✅ indicator
- ✅ "PHASE 4: MONITORING" → Receives >10 pose updates
- ✅ "PHASE 5: NAVIGATION" → Navigation command sent
- ✅ "PHASE 6: CLOSE SLAM" → SLAM closed cleanly
- ✅ "✅ SLAM TEST COMPLETE" → Final message printed
- ✅ Map file exists: `ls -lh /home/unitree/test_simple.pcd`

---

**Last Updated**: Feb 4, 2026 - Test script finalized with verified Feb 3 format  
**Next Check-in**: After running test - update with results
