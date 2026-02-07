# 🤖 SLAM MAP BUILDING - Quick Start Guide

## Your Goal Today

✅ Verify that SLAM mapping APIs actually work with your robot
✅ Build ONE real map you can reuse for navigation tests
✅ Test if API 1102 supports heading/rotation at destination

**Duration**: 5-10 minutes active time + robot movement time

---

## What You'll Do

### Phase 1: Build & Save Map (2-3 minutes)

```bash
python3 test_map_build_with_joystick.py
```

This script will:

1. **START_MAPPING** (API 1801) - Turns on LiDAR, starts capturing
2. **Wait for you** - You take joystick and drive robot around for 30-60 seconds
3. **SAVE_MAP** (API 1802) - Writes the captured data as a PCD file on robot
4. **VERIFY** - Checks that the map file was created
5. **LOAD_MAP** (API 1804) - Verifies the saved map can be reloaded

**What to do during driving phase**:
- Take your joystick/gamepad
- Move robot forward, backward, left, right
- Turn in circles
- Cover as much area as possible (50+ square meters is ideal)
- Return to starting position
- Press ENTER to continue

**Expected output**:
```
✅ START_MAPPING successful - LiDAR is now capturing
✅ Recording complete (45.3 seconds of LiDAR data captured)
✅ SAVE_MAP successful - map written to robot filesystem
✅ LOAD_MAP successful - map loaded into SLAM system
```

---

### Phase 2: Test Heading Support (2-3 minutes)

After Phase 1 completes successfully:

```bash
python3 test_api_1102_heading.py --map test_map
```

This script will:

1. **LOAD_MAP** - Loads your saved map
2. **Move to 4 points** - Navigates to different positions with different headings (0°, 90°, 180°, 270°)
3. **You observe** - Watch if robot rotates to match the specified heading

**What to observe**:
- Position robot at origin (0,0) 
- Watch robot's RED tail light for orientation
- At each destination, check if robot rotates to the specified heading

**Expected outcomes**:
- ✅ **If heading works**: Robot rotates to each specified direction
- ❌ **If heading doesn't work**: Robot always faces the movement direction

This tells us whether Phase C (waypoint navigation) needs special heading handling.

---

## Step-by-Step

### Step 1: Prepare

```bash
cd /root/G1/unitree_sdk2

# Make sure scripts are executable
chmod +x test_map_build_with_joystick.py
chmod +x test_api_1102_heading.py

# Verify joystick is connected (optional)
ls /dev/input/js0  # Should exist if joystick connected
```

### Step 2: Build Map

```bash
# Terminal 1 - Run the map builder
python3 test_map_build_with_joystick.py --name my_room

# Wait for prompts:
# "STEP 1: Starting SLAM Mapping" - Robot starts capturing
# "STEP 2: Drive Robot with Joystick" - YOU take joystick
#    * Move robot around for 30-60 seconds
#    * Press ENTER when done
# "STEP 3: Saving Map to File" - Script saves the map
# "STEP 4: Verifying PCD File" - Script checks file
# "STEP 5: Loading Map Back" - Script loads map to verify
```

### Step 3: Test Heading

```bash
# After map building completes successfully:
python3 test_api_1102_heading.py --map my_room

# Follow prompts:
# "Position robot at map origin" - Put robot at starting point
# Press ENTER to begin navigation tests
# Watch robot rotate (or not) to specified headings
```

---

## Troubleshooting

### Map building stops with error

**Error: "START_MAPPING failed"**
- Robot firmware doesn't support SLAM mapping
- Check: Is SLAM module enabled in robot settings?
- Try: Restart robot and retry

**Error: "SAVE_MAP failed"**
- Check: Is `/home/unitree/` writable on robot?
- Try: Make sure robot has enough free space (`df -h` on robot)

**Error: "Connection failed"**
- Check: Is robot on WiFi? (`ping 192.168.86.3`)
- Try: Restart robot and re-run script

### Heading test shows heading doesn't work

This is OK! It just means API 1102 doesn't support quaternion parameters.

**Solution for Phase C**:
- Use API 1102 to move robot to position
- After movement completes, use API 7105 (SET_VELOCITY) to rotate to desired heading
- This is a 2-step process instead of 1-step, but it works

---

## Output Files

After successful map building:

```
/home/unitree/my_room.pcd    # On robot
~/maps/my_room.pcd           # Local copy (if accessible)
```

You can:
- Use this map for all future waypoint tests
- Visualize it with PCL viewer: `pcl_viewer my_room.pcd`
- Load it with API 1804 for any navigation test

---

## What Gets Verified

After these tests, you'll know:

| Feature | Status | Test |
|---------|--------|------|
| API 1801 (START_MAPPING) | ✅ or ❌ | Map Builder Phase 1 |
| API 1802 (SAVE_MAP) | ✅ or ❌ | Map Builder Phase 3 |
| API 1804 (LOAD_MAP) | ✅ or ❌ | Map Builder Phase 5 |
| API 1102 (NAVIGATE_TO) | ✅ or ❌ | Heading Test |
| Heading Support | ✅ or ❌ | Heading Test observation |

---

## Next Steps

**After Phase 1 succeeds** (map building):
- You have a real map
- You know APIs 1801, 1802, 1804 work
- Ready for Phase A (waypoint backend)

**After Phase 2 succeeds** (heading test):
- You know if API 1102 supports heading
- If YES: Phase C implementation is straightforward
- If NO: Phase C needs 2-step navigation (move + rotate)

**Then implement**:
- Phase A: Waypoint storage (SQLite or JSON)
- Phase B: Web API endpoints (CRUD operations)
- Phase C: Navigation logic (API 1102 with heading handling)
- Phase D: Web UI for waypoints
- Phase E: Session persistence

---

## Key Insights

**Why we do this first**:
- Don't rebuild complex code from scratch if APIs don't work
- Verify each API independently first
- No "black box" debugging through full system

**Fast feedback loop**:
- Each test takes 2-3 minutes
- Clear pass/fail for each API
- Clear action items for any failures

**What you'll learn**:
- SLAM mapping works on your robot (or doesn't)
- How long map building takes
- Whether heading is supported (affects waypoint feature)
- Map file format and size

---

## Commands Reference

```bash
# Build map
python3 test_map_build_with_joystick.py --name <map_name>

# Test heading
python3 test_api_1102_heading.py --map <map_name>

# Check robot connectivity
ping 192.168.86.3

# List maps on robot (if SSH access)
ssh root@192.168.86.3 ls -lh /home/unitree/*.pcd

# View PCD file locally (if installed)
pcl_viewer /path/to/map.pcd
```

---

## Estimated Timeline

| Phase | Duration | What Happens |
|-------|----------|--------------|
| Prep | 1 min | Make scripts executable |
| Build Map - Start | 30 sec | API 1801 called, LiDAR starts |
| Build Map - Drive | 30-60 sec | **You drive robot with joystick** |
| Build Map - Save | 30 sec | API 1802 called, map written |
| Build Map - Verify | 30 sec | Check file created, API 1804 test |
| Heading Test - Setup | 1 min | Position robot at origin |
| Heading Test - Navigate | 2-3 min | 4 navigation tests, 30 sec each |
| **Total** | **5-10 min** | |

---

**Ready?** Start with:

```bash
python3 test_map_build_with_joystick.py --name my_first_map
```

Let me know the results! 🚀
