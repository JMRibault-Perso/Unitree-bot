# ✅ API Testing Infrastructure - Created Feb 5, 2026

## What Was Just Created

You now have **two focused test scripts** to verify that SLAM APIs actually work before implementing any complex system.

No system rebuild. No complex architecture. Just:
1. **Test the APIs work** ✅
2. **Build ONE map** ✅
3. **Test heading support** ✅
4. **Then implement** the waypoint system

---

## The Two Test Scripts

### 1. `test_map_build_with_joystick.py` (16 KB)

**Purpose**: Complete SLAM mapping workflow with joystick control

**What it does**:
```
START_MAPPING (API 1801)
    ↓
[You drive robot with joystick for 30-60 seconds]
    ↓
SAVE_MAP (API 1802)
    ↓
VERIFY PCD FILE created
    ↓
LOAD_MAP (API 1804) - verify it works
```

**Run it**:
```bash
python3 test_map_build_with_joystick.py --name my_room
```

**Output**:
- Saves `/home/unitree/my_room.pcd` on robot
- If successful, you have a real map to use for all future tests
- Confirms APIs 1801, 1802, 1804 are working

**Duration**: ~3 minutes (includes your joystick driving time)

---

### 2. `test_api_1102_heading.py` (13 KB)

**Purpose**: Test if API 1102 (NAVIGATE_TO) supports heading/quaternion

**What it does**:
```
LOAD the saved map
    ↓
Move robot to point A with heading 0° (facing East)
    ↓
Move robot to point B with heading 90° (facing North)
    ↓
Move robot to point C with heading 180° (facing West)
    ↓
Move robot to point D with heading 270° (facing South)
    ↓
[You observe if robot rotates to each heading]
```

**Run it**:
```bash
python3 test_api_1102_heading.py --map my_room
```

**What to observe**:
- ✅ **If heading works**: Robot rotates to each specified direction
- ❌ **If heading doesn't work**: Robot always faces movement direction

**Duration**: ~5 minutes (4 movement tests × 30 seconds each + setup)

---

## Why These Two Tests

### Test 1 (Map Building) Answers

| Question | Test Phase |
|----------|-----------|
| Does API 1801 (START_MAPPING) work? | START phase |
| Does API 1802 (SAVE_MAP) work? | SAVE phase |
| Can we actually save maps as PCD files? | VERIFY phase |
| Does API 1804 (LOAD_MAP) work? | LOAD phase |
| How long does mapping take? | Your observation |
| How large is a map file? | File verification |

**Critical**: If any of these fail, you know NOT to implement waypoints yet. APIs need fixing first.

### Test 2 (Heading Support) Answers

| Question | Test Phase |
|----------|-----------|
| Does API 1102 accept quaternion parameters? | Parameter test |
| Does robot rotate to match heading? | Observation |
| How is heading represented? | Response analysis |
| Do we need 2-step navigation? | YES/NO decision |

**Critical**: This decides how Phase C (navigation logic) is implemented.

---

## The Testing Philosophy

**Old approach** (don't do this):
- Implement full waypoint system
- Try to test it
- When heading doesn't work, debug entire system
- Takes weeks to find the problem

**New approach** (what we're doing):
- Test each API independently first
- If API fails, fix before implementing system
- If API works, implement with confidence
- Takes 5-10 minutes to verify everything

---

## What Happens Next

### Best Case (Both tests pass ✅)

```
Test 1: Map building works
Test 2: Heading is supported

↓

Implement Phase A (Waypoint Backend):
  - Store waypoints with (x, y, heading)
  - Keep them in JSON file or SQLite
  - Include heading in every waypoint

Phase C will be straightforward:
  - Use API 1102 with quaternion for heading
  - Robot will rotate as desired
```

### Heading Not Supported (Test 2 shows ❌)

```
Test 1: Map building works
Test 2: Heading is NOT supported

↓

Implement Phase C differently:
  - API 1102 moves robot to position
  - Then use API 7105 (velocity control) to rotate
  - Two-step navigation for each waypoint

This still works, just needs extra step
```

### Map Building Fails (Test 1 shows ❌)

```
Test 1: Map building fails

↓

STOP - don't implement anything
Check robot firmware
Contact Unitree support
Fix the API first
```

---

## Running the Tests

### Quick Start

```bash
# Terminal 1 - Run map builder
cd /root/G1/unitree_sdk2
python3 test_map_build_with_joystick.py

# When prompted, take joystick and drive robot for 30-60 seconds
# When complete, run:

# Terminal 2 - Test heading
python3 test_api_1102_heading.py --map test_map
```

### With Custom Robot IP

```bash
python3 test_map_build_with_joystick.py --robot-ip 192.168.1.100 --name my_room
python3 test_api_1102_heading.py --robot-ip 192.168.1.100 --map my_room
```

### Expected Success Messages

**Test 1**:
```
✅ START_MAPPING successful - LiDAR is now capturing
✅ Recording complete (45.3 seconds of LiDAR data captured)
✅ SAVE_MAP successful - map written to robot filesystem
✅ LOAD_MAP successful - map loaded into SLAM system
```

**Test 2**:
```
✅ Map loaded successfully
✅ Navigation started
✅ Should now be at Point A
   - Check if robot is facing 0° direction
   - If facing movement direction: heading NOT supported
   - If facing 0°: heading IS supported ✅
```

---

## FAQ

**Q: Do I need to rebuild anything?**
A: No! These are standalone test scripts. Just run them.

**Q: What if map building fails?**
A: Check robot firmware. If APIs don't work, there's no point implementing waypoints yet.

**Q: What if heading test fails?**
A: It's OK. We'll implement 2-step navigation (move → rotate). Still works, just different.

**Q: How many maps should I build?**
A: One is enough for testing. Build more later if testing passes.

**Q: Can I reuse the same map?**
A: Yes! That's why we verify API 1804 (LOAD_MAP) works.

**Q: What about that PCD file?**
A: It's a point cloud format. You can visualize it with: `pcl_viewer my_room.pcd`

**Q: Should I start with heading test?**
A: No! Always do map building first. Heading test needs a loaded map.

---

## Next Steps After Testing

### If Everything Passes ✅

1. **Keep the map file**: `my_room.pcd` is your test map
2. **Note the API results**: Which heading approach (1-step vs 2-step)
3. **Start Phase A**: Implement waypoint storage
4. **Reference these tests**: Use them as examples for Phase B/C/D

### If Something Fails ❌

1. **Check the error message**: Script will show what failed
2. **Debug one API**: Don't try to fix multiple things at once
3. **Consult documentation**: Reference guide in KNOWLEDGE_BASE.md
4. **Contact support**: If firmware issue, may need update

---

## Files Created

| File | Size | Purpose |
|------|------|---------|
| `test_map_build_with_joystick.py` | 16 KB | Interactive map building with joystick |
| `test_api_1102_heading.py` | 13 KB | Test heading support in navigation |
| `MAP_BUILDING_QUICK_START.md` | 6 KB | This quick-start guide |
| `API_TESTING_SUMMARY.md` | This file | What was created and why |

---

## Key Takeaway

**Before implementing the waypoint system**, verify:
1. ✅ Can we build maps? (Test 1)
2. ✅ Can we load maps? (Test 1 phase 5)
3. ✅ Does heading work? (Test 2)

Once these three questions are answered, Phase A-E implementation is straightforward.

**No guessing. No blind coding. Just verification.**

---

**Ready to test?**

```bash
python3 test_map_build_with_joystick.py --name test_map
```

Good luck! 🚀
