# SLAM Relocation Testing Guide

## Overview
Now that you have a reusable room.pcd map, we can test the relocation system. Relocation means the robot tracks its position as it moves around the mapped environment.

## Quick Start

### Step 1: Check if relocation topics are active
```bash
cd /root/G1/unitree_sdk2/g1_tests/slam
python3 check_slam_topics.py
```

This will show which SLAM topics are publishing:
- ✅ `rt/unitree/slam_mapping/odom` - Publishing during mapping
- ✅ `rt/unitree/slam_relocation/odom` - Publishing during navigation/relocation
- ✅ `rt/lf/sportmodestate` - FSM state with position (fallback)

**Expected output if relocation works:**
- relocation topic should show message counts increasing
- sportmodestate should also be active

### Step 2: Load map and monitor position
```bash
python3 test_relocation.py
```

This script will:
1. Load room.pcd map
2. Initialize robot position at origin (0, 0, 0)
3. Monitor position updates for 60 seconds
4. Display real-time position as you move the robot

**What to do during the 60 seconds:**
- Move robot forward/backward (observe X/Y position change)
- Turn the robot left/right (observe heading change)
- Move in circles (observe position corrections)

**What you should see:**
- Position X, Y, Z values updating in real-time
- Heading angle changing when you rotate
- Distance from origin increasing as you move away

## Understanding the Output

### Position Display
```
📍 X=   1.234m  Y=   0.567m  Z=   0.000m  Heading= 45.2°  ΔDist= 1.389m  Updates=  120
```

- **X, Y, Z**: Robot position in meters (origin is where you loaded map)
- **Heading**: Robot rotation in degrees (0° = facing initial direction)
- **ΔDist**: Distance from starting position
- **Updates**: Total odometry messages received

### Summary Report
```
✅ RELOCATION WORKING
   - Robot received 1200 position updates
   - Position tracking is active
   - Movement detected:
     - Robot moved 2.567m
     - Heading changed 45.2°
     - Position updates responding to movement ✅
```

## Troubleshooting

### Problem: "Updates = 0 - no odometry"

**Cause:** Relocation topics not publishing

**Solutions:**
1. Verify map loaded correctly:
   ```bash
   ls -lh /home/unitree/room.pcd
   ```

2. Check robot is in RUN state:
   ```bash
   python3 ../test_fsm_state.py
   # Should show: fsm_id in (500, 501) or 801
   ```

3. Check if mapping still active (should be OFF):
   ```bash
   python3 check_slam_topics.py
   # mapping_odom should be INACTIVE, relocation_odom should be ACTIVE
   ```

### Problem: "Position not changing when I move robot"

**Cause:** Robot may be held in place or relocation not tracking movement

**Solutions:**
1. Verify robot can move:
   - Try walking robot with joystick
   - Check if it responds to commands

2. Check relocation mode:
   ```bash
   python3 check_slam_topics.py
   # Verify relocation_odom is receiving messages
   ```

3. Try moving robot further/faster
   - Small movements may not trigger position updates
   - Rotate the robot (heading change is easier to see)

### Problem: "Position jumps around randomly"

**Cause:** Relocation drift correction or sensor noise

**Solutions:**
1. Move slowly and deliberately
2. Keep robot in areas that match the mapped area
3. Move in patterns (straight lines, circles)
4. Try again - relocation may need time to stabilize

## Advanced Testing

### Test 1: Position Accuracy
After running `test_relocation.py`:
1. Note the final position
2. Walk robot to known location (corner, specific point)
3. Run test again - initial position should be similar

### Test 2: Heading Verification
1. Load map with robot facing north (0°)
2. Rotate 90° clockwise - heading should be ~90°
3. Rotate another 90° - heading should be ~180°
4. Continue rotating - verify heading matches actual rotation

### Test 3: Map Boundaries
1. Load map
2. Try moving robot outside the original mapped area
3. Observe if position tracking degrades or becomes inaccurate
4. Return to mapped area - position should stabilize again

## Expected Behavior

### Mapping Mode (API 1801 active)
- `rt/unitree/slam_mapping/odom` publishing (LiDAR capturing)
- `rt/unitree/slam_relocation/odom` NOT publishing
- Position may not be accurate

### Relocation Mode (API 1804 active - map loaded)
- `rt/unitree/slam_relocation/odom` publishing (position tracking)
- Position updates as robot moves
- Position corrections as relocation algorithm tracks movement

## Performance Metrics

### Good Performance
- **Update rate:** 20+ messages/sec (from relocation topic)
- **Position update time:** <50ms
- **Heading accuracy:** ±5° of actual rotation
- **Position drift:** <10cm over 1 minute of movement

### Acceptable Performance
- **Update rate:** 10+ messages/sec
- **Position update time:** <100ms
- **Heading accuracy:** ±10° of actual rotation
- **Position drift:** <20cm over 1 minute

### Poor Performance
- **Update rate:** <5 messages/sec (or 0)
- **No heading change** when rotating
- **No position change** when moving
- **Large jumps** in position (<10cm movements cause 1m+ jumps)

## Next Steps (After Relocation Verification)

Once relocation is working, you can:

1. **Test Navigation API (1102)**
   ```bash
   python3 test_navigation_v2.py --target-x 1.0 --target-y 0.5
   ```

2. **Test Waypoint Navigation**
   - Use loaded map to navigate between known positions
   - Verify robot reaches target coordinates

3. **Build Waypoint System** (Phase A-E implementation)
   - Store waypoints with coordinates (from relocation)
   - Navigate between waypoints
   - Persist waypoints across robot restart

## Data Collection

The test saves data to: `/root/G1/unitree_sdk2/data/test_data/maps/room_relocation.json`

Contains:
- All position samples (timestamp, x, y, z, heading)
- Final position
- Distance traveled
- Total updates received

Use this data to:
- Plot position history
- Verify no large position jumps
- Calculate drift over time
- Detect relocation corrections

---

**Status:** Test infrastructure ready. Run `python3 test_relocation.py` to verify relocation is working with room.pcd map.
