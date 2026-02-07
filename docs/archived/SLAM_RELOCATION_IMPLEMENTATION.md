# SLAM Relocation Testing - Implementation Complete

## Overview
You now have a complete testing infrastructure to verify SLAM relocation (position tracking) works with your room.pcd map.

## What's Been Added

### 1. Relocation Test Script
**File:** `g1_tests/slam/test_relocation.py`

A complete script that:
- Loads room.pcd map
- Initializes position at origin (0, 0, 0)  
- Monitors real-time position updates for 60 seconds
- Displays X, Y, Z, Heading as you move the robot
- Saves data for analysis

**Usage:**
```bash
cd /root/G1/unitree_sdk2/g1_tests/slam
python3 test_relocation.py
```

**Output:**
```
📍 X=   1.234m  Y=   0.567m  Z=   0.000m  Heading= 45.2°  ΔDist= 1.389m  Updates=  120
```

### 2. Topics Monitoring Script
**File:** `g1_tests/slam/check_slam_topics.py`

Checks which SLAM topics are publishing:
- rt/unitree/slam_mapping/odom (mapping phase)
- rt/unitree/slam_relocation/odom (navigation phase) 
- rt/lf/sportmodestate (fallback FSM state)
- rt/unitree/slam_info (status info)

**Usage:**
```bash
python3 check_slam_topics.py
```

**Diagnostic Output:**
Shows which topics are active and how many messages received.

### 3. Robot Controller Enhancement
**File:** `g1_app/core/robot_controller.py`

Added position tracking:
- `current_position` dict with x, y, z, heading, timestamp
- `current_position_updates` counter to track relocation activity
- Subscription to `rt/unitree/slam_relocation/odom` topic
- Quaternion to heading angle conversion

### 4. Web API Endpoint
**File:** `g1_app/ui/web_server.py`

New endpoint: `/api/slam/current_position`

Get current position programmatically:
```bash
curl http://192.168.86.2:8080/api/slam/current_position
```

Response:
```json
{
  "success": true,
  "position": {
    "x": 1.234,
    "y": 0.567,
    "z": 0.000,
    "heading": 45.2
  },
  "updates_received": 120,
  "has_relocation": true,
  "timestamp": 1707123456.789
}
```

### 5. Testing Guide
**File:** `SLAM_RELOCATION_TESTING.md`

Complete guide with:
- Step-by-step testing procedure
- Expected output interpretation
- Troubleshooting common issues
- Performance metrics
- Advanced testing scenarios

## Testing Workflow

### Step 1: Check Topics Are Publishing
```bash
python3 g1_tests/slam/check_slam_topics.py
```

**Expected:** See updates for `rt/unitree/slam_relocation/odom`

### Step 2: Run Relocation Test
```bash
python3 g1_tests/slam/test_relocation.py
```

**During 60 seconds:**
- Move robot forward/backward
- Turn left/right
- Move in circles
- Return to starting position

**Expected:** Position values updating in real-time

### Step 3: Interpret Results
```
✅ RELOCATION WORKING
   - Robot received 1200 position updates
   - Movement detected:
     - Robot moved 2.567m
     - Heading changed 45.2°
     - Position updates responding to movement ✅
```

## How It Works

### Position Tracking Architecture
```
Robot Hardware
    ↓
LiDAR + IMU sensors
    ↓
On-robot SLAM engine (PC1)
    ↓
rt/unitree/slam_relocation/odom (published every 50ms @ 20Hz)
    ↓
Your PC (receives via WebRTC)
    ↓
RobotController.current_position (updated in real-time)
    ↓
Web API /api/slam/current_position (accessible from UI/curl)
```

### Key Topics
- **Mapping phase:** `rt/unitree/slam_mapping/odom` - Position while capturing LiDAR
- **Navigation phase:** `rt/unitree/slam_relocation/odom` - Position while navigating map
- **Fallback:** `rt/lf/sportmodestate` - Robot state including position (if relocation unavailable)

## Verification Checklist

✅ room.pcd built successfully  
✅ test_relocation.py script created  
✅ check_slam_topics.py script created  
✅ RobotController tracks current_position  
✅ Web API endpoint added  
✅ Position updates monitored in real-time  

### Known Relocation Issue (Handle in Flow)
- **LOAD_MAP can return**: "The current location matching degree is low."
- **Implication**: Relocalization failed to match the current pose.
- **Handling**: Prompt user to reposition/rotate the robot, then retry LOAD_MAP.

## Next Steps (After Verification)

1. **Verify relocation works** - Run test_relocation.py and move robot
2. **Test position accuracy** - Load map, move to known location, verify position  
3. **Test heading accuracy** - Rotate robot, verify heading matches rotation
4. **Implement waypoint system** (Phase A-E)
   - Store waypoints with coordinates
   - Load waypoints and navigate between them
   - Persist across restart

## Performance Expectations

### Good Performance
- **Update frequency:** 20 Hz (50ms per update)
- **Position accuracy:** ±10cm
- **Heading accuracy:** ±5°
- **Update latency:** <100ms
- **Total updates in 60s:** 1000+

### Acceptable Performance
- **Update frequency:** 10 Hz
- **Position accuracy:** ±20cm
- **Heading accuracy:** ±10°
- **Update latency:** <200ms
- **Total updates in 60s:** 500+

### Problems
- **No updates:** Relocation not active - check map loaded
- **Position jumps:** Large random movements - relocation initializing
- **No heading change:** Orientation not tracked - may need longer movements

## File Locations

```
/root/G1/unitree_sdk2/
├── g1_tests/slam/
│   ├── test_relocation.py          ← Main relocation test
│   ├── check_slam_topics.py        ← Topic monitoring  
│   ├── simple_map_build.py         ← Reference map builder
│   └── ...                          [other SLAM tests]
├── g1_app/
│   ├── core/
│   │   └── robot_controller.py     ← Position tracking added
│   └── ui/
│       └── web_server.py           ← Position API endpoint added
├── test_maps/
│   ├── room.pcd                    ← Your map file
│   └── room_relocation.json        ← Test data (generated)
└── SLAM_RELOCATION_TESTING.md      ← Full testing guide
```

## Troubleshooting

### "Updates = 0"
**Cause:** Relocation odometry not publishing

**Solutions:**
1. Check map loaded: `ls -lh /home/unitree/room.pcd`
2. Verify robot state: Check FSM is LOCK_STAND/RUN
3. Check relocation topics: Run `check_slam_topics.py`

### "Position not changing"
**Cause:** Robot not moving or relocation not tracking movement

**Solutions:**
1. Move robot further/faster
2. Rotate robot (easier to detect heading change)
3. Check if relocation_odom is receiving messages

### "Position jumping around"
**Cause:** Normal during relocation initialization

**Solutions:**
1. Move slowly and deliberately
2. Try again - relocation may need time to stabilize
3. Verify you're in the mapped area

## Integration with Phase A-E

Once relocation is verified:

**Phase A:** Waypoint backend
- Store waypoint coords from current_position API
- Save to database/JSON

**Phase B:** Web API
- GET /api/waypoints (list all)
- POST /api/waypoints (create new from current position)

**Phase C:** Navigation
- Use SLAM_API['NAVIGATE'] to move between waypoints
- Monitor position with /api/slam/current_position

**Phase D:** Web UI
- Display current position in real-time
- Show waypoint list
- Navigate between waypoints

**Phase E:** Persistence
- Save waypoints across restart
- Load and resume navigation

---

**Status:** ✅ Complete. Ready to test SLAM relocation with room.pcd map.

Run: `python3 g1_tests/slam/test_relocation.py`
