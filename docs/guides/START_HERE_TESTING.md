# 🚀 API TESTING - Your 10-Minute Verification Plan

## The Goal

You do NOT want to spend weeks building a complex system just to find out APIs don't work.

**Instead**: Spend 10 minutes verifying the APIs work first, THEN implement the system.

---

## Your 3 Commands to Run

### Command 1: Build a Real Map

```bash
cd /root/G1/unitree_sdk2
python3 test_map_build_with_joystick.py --name my_room
```

**What to expect**:
- Script asks you to take joystick and drive robot (30-60 seconds)
- When complete, you'll see:
  ```
  ✅ START_MAPPING successful - LiDAR is now capturing
  ✅ Recording complete (X seconds of LiDAR data captured)
  ✅ SAVE_MAP successful - map written to robot filesystem
  ✅ LOAD_MAP successful - map loaded into SLAM system
  ```
- If this succeeds: APIs 1801, 1802, 1804 are WORKING ✅

**Time needed**: ~3 minutes (including your driving time)

---

### Command 2: Test Heading Support

```bash
python3 test_api_1102_heading.py --map my_room
```

**What to expect**:
- Robot moves to 4 positions with different headings (0°, 90°, 180°, 270°)
- You observe if robot rotates to match each heading
- Watch the RED light on robot's rear end

**Two possible outcomes**:

**Outcome A: Heading IS Supported** ✅
- Robot rotates to match each specified heading
- Phase C will be straightforward (1-step navigation with heading)

**Outcome B: Heading NOT Supported** ❌
- Robot always faces the movement direction
- Phase C will need 2-step navigation (move → rotate)
- Still works, just slightly more complex

**Time needed**: ~5 minutes

---

## What You'll Know After These Tests

| Question | Test | Answer |
|----------|------|--------|
| Does API 1801 (START_MAPPING) work? | Test 1 | ✅ YES or ❌ NO |
| Does API 1802 (SAVE_MAP) work? | Test 1 | ✅ YES or ❌ NO |
| Does API 1804 (LOAD_MAP) work? | Test 1 | ✅ YES or ❌ NO |
| Does API 1102 (NAVIGATE_TO) work? | Test 2 | ✅ YES or ❌ NO |
| Does API 1102 support heading? | Test 2 observation | ✅ YES or ❌ NO |

---

## Why This Matters

**Old approach** (bad):
1. Spend weeks building waypoint system
2. Try to test it
3. Find out API 1801 doesn't work
4. Go back and fix everything
5. Months of wasted time

**New approach** (good):
1. Spend 10 minutes testing APIs
2. If APIs work → Implement system confidently
3. If API fails → Know immediately to fix before implementing
4. Much faster overall

---

## Next Steps After Testing

### If All Tests Pass ✅

You're ready to implement:
1. **Phase A**: Waypoint storage backend
2. **Phase B**: Web API endpoints
3. **Phase C**: Navigation logic (with or without heading step, depending on Test 2)
4. **Phase D**: Web UI
5. **Phase E**: Session persistence

### If Any Test Fails ❌

1. **API failed**: Don't implement anything yet. Debug the API first.
2. **Joystick not working**: Verify joystick is connected: `ls /dev/input/js0`
3. **Robot not responding**: Check WiFi connection: `ping 192.168.86.3`
4. **PCD file not created**: Check robot filesystem space: SSH and run `df -h`

---

## The Exact Commands

Copy and paste these in order:

```bash
# Step 1: Navigate to project directory
cd /root/G1/unitree_sdk2

# Step 2: Build a map (takes ~3 minutes, includes your driving time)
python3 test_map_build_with_joystick.py --name my_room

# When Step 2 completes successfully, run:

# Step 3: Test heading support (takes ~5 minutes)
python3 test_api_1102_heading.py --map my_room
```

That's it! After these 3 commands (10 minutes total):
- ✅ You have a real map file
- ✅ You know which APIs work
- ✅ You know if heading is supported
- ✅ You can confidently implement Phase A-E

---

## Files Reference

| File | Purpose |
|------|---------|
| `test_map_build_with_joystick.py` | Interactive map building with joystick |
| `test_api_1102_heading.py` | Test heading support in navigation |
| `MAP_BUILDING_QUICK_START.md` | Detailed step-by-step guide |
| `API_TESTING_SUMMARY.md` | What was created and why |
| `KNOWLEDGE_BASE.md` | API reference (in main directory) |

---

## Expected Results

### Test 1 Success
```
✅ START_MAPPING successful - LiDAR is now capturing
[You drive robot here for 30-60 seconds]
✅ Recording complete (42.5 seconds of LiDAR data captured)
✅ SAVE_MAP successful - map written to robot filesystem
✅ LOAD_MAP successful - map loaded into SLAM system

====================================================================
✅ ALL TESTS PASSED!

Summary:
  ✅ START_MAPPING (API 1801) - working
  ✅ SAVE_MAP (API 1802) - working
  ✅ LOAD_MAP (API 1804) - working
```

### Test 2 Success
```
[Robot moves to each point, you observe rotation]
✅ Navigation started
⏳ Waiting for robot to reach destination (30 seconds)...
✅ Should now be at Point A
   - Check if robot is facing 0° direction
   
[Repeat for points B, C, D]

✅ HEADING TEST SEQUENCE COMPLETE

Observations:
  ✅ If robot rotated to each heading: API 1102 SUPPORTS HEADING
```

---

## Key Points

1. **No complex system rebuild required** - just test individual APIs
2. **Fast feedback loop** - 10 minutes, not hours
3. **Clear pass/fail for each API** - no guessing
4. **Results determine Phase C approach** - heading support or 2-step navigation
5. **You have a real map for all future tests** - saves time for Phase A-E testing

---

## Ready?

```bash
cd /root/G1/unitree_sdk2
python3 test_map_build_with_joystick.py --name my_room
```

Run this now. Tell me the results! 🚀
