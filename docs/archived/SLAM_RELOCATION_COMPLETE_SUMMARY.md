# SLAM Relocation Testing - Complete Summary

## What You Have Now

### ✅ Room Map
- **File:** `/home/unitree/room.pcd` (on robot)
- **Status:** Built and verified with simple_map_build.py
- **Ready for:** Relocation testing and waypoint navigation

### ✅ Test Scripts

1. **test_relocation.py** - Main relocation test
   - Loads map and monitors position for 60 seconds
   - Displays real-time X, Y, Z, Heading
   - Shows update statistics
   - Saves test data to JSON

2. **check_slam_topics.py** - Topic diagnostic
   - Shows which SLAM topics are publishing
   - Counts messages on each topic
   - Helps diagnose relocation issues

### ✅ Robot Controller Enhancement
- Tracks `current_position` (x, y, z, heading)
- Counts `current_position_updates`
- Subscribes to `rt/unitree/slam_relocation/odom`
- Converts quaternions to heading angles

### ✅ Web API Endpoint
```
GET /api/slam/current_position
```
Returns current position as JSON (usable from web UI or curl)

### ✅ HTML Position Widget
**File:** SLAM_POSITION_WIDGET.html
- Real-time position display
- Heading visual indicator
- Update frequency tracking
- Can be embedded in web dashboard

### ✅ Documentation
1. **SLAM_RELOCATION_QUICKSTART.md** - 5-minute guide
2. **SLAM_RELOCATION_TESTING.md** - Complete testing guide
3. **SLAM_RELOCATION_IMPLEMENTATION.md** - Technical details

## How to Test Relocation

### Step 1: Verify Topics Publishing
```bash
cd /root/G1/unitree_sdk2/G1_tests/slam
python3 check_slam_topics.py
```

Wait 15 seconds and look for:
- ✅ `rt/unitree/slam_relocation/odom` - should show message count
- ✅ `rt/lf/sportmodestate` - should show message count

If you see 0 messages on relocation topic:
1. Check map loaded: `ls -lh /home/unitree/room.pcd`
2. Verify robot FSM state (should be RUN or LOCK_STAND)
3. Check if mapping is still active (should be OFF)

### Step 2: Run Full Relocation Test
```bash
python3 test_relocation.py
```

**During 60-second window:**
- Walk robot forward/backward
- Turn left/right  
- Move in circles
- Return to starting position

**Monitor the display:**
```
📍 X=   1.234m  Y=   0.567m  Z=   0.000m  Heading= 45.2°  ΔDist= 1.389m  Updates=  120
```

**Expected results:**
- Position values change as you move
- Heading changes as you rotate
- Update counter increases (should reach 1000+ for 60 seconds)

### Step 3: Interpret Results

**Good Results:**
```
✅ RELOCATION WORKING
   - Robot received 1200 position updates
   - Movement detected:
     - Robot moved 2.567m
     - Heading changed 45.2°
     - Position updates responding to movement ✅
```

**No Updates:**
```
❌ RELOCATION NOT WORKING
   - No position updates received
   - Check: Is map loaded? Is robot in RUN state? Is relocation_odom topic publishing?
```

## Architecture

### Position Data Flow
```
Robot LiDAR + IMU
    ↓
On-Robot SLAM Engine (PC1)
    ↓
rt/unitree/slam_relocation/odom (20 Hz, 50ms interval)
    ↓
WebRTC Channel (encrypted)
    ↓
Your PC - RobotController.current_position
    ↓
Web API: /api/slam/current_position
    ↓
Web UI: SLAM_POSITION_WIDGET.html (displays live)
```

### Topics Used

| Topic | Purpose | When Active | Update Rate |
|-------|---------|------------|-------------|
| `rt/unitree/slam_mapping/odom` | Position during mapping | API 1801 active | 20 Hz |
| `rt/unitree/slam_relocation/odom` | Position during navigation | API 1804 active | 20 Hz |
| `rt/lf/sportmodestate` | Fallback FSM state | Always | ~30 Hz |
| `rt/slam_info` | Status info | Active mapping | Variable |

## File Reference

```
/root/G1/unitree_sdk2/
├── G1_tests/slam/
│   ├── test_relocation.py              ← Main test script
│   ├── check_slam_topics.py            ← Diagnostic tool
│   ├── simple_map_build.py             ← Reference (map builder)
│   └── [other SLAM tests]
├── g1_app/
│   ├── core/
│   │   └── robot_controller.py         ← Position tracking added (lines 73-75)
│   └── ui/
│       └── web_server.py               ← Position endpoint added (lines 1820-1845)
├── test_maps/
│   ├── room.pcd                        ← Your map (on robot at /home/unitree/room.pcd)
│   └── room_relocation.json            ← Test data (generated after each run)
├── SLAM_POSITION_WIDGET.html           ← Web UI widget
├── SLAM_RELOCATION_QUICKSTART.md       ← Quick start guide
├── SLAM_RELOCATION_TESTING.md          ← Complete guide
└── SLAM_RELOCATION_IMPLEMENTATION.md   ← Technical details
```

## Expected Performance

### Good Performance
- **Update rate:** 20 Hz (updates every 50ms)
- **Position accuracy:** ±10cm
- **Heading accuracy:** ±5°
- **Updates in 60 seconds:** 1000-1200
- **Latency:** <100ms

### Acceptable
- **Update rate:** 10 Hz
- **Position accuracy:** ±20cm
- **Heading accuracy:** ±10°
- **Updates in 60 seconds:** 500-600
- **Latency:** <200ms

### Problem Indicators
- **0 updates:** Relocation not active or topic not publishing
- **Position doesn't change:** Robot not moving or relocation not tracking
- **Large random jumps:** Relocation initializing or drift correction

## Web Integration

### Add to Web Dashboard
```html
<!-- In your web UI template -->
<div id="position-widget">
    <!-- Copy content from SLAM_POSITION_WIDGET.html -->
</div>

<script>
    // Monitor will auto-start on page load
    // Updates position every 500ms
    // Shows real-time X, Y, Z, Heading
</script>
```

### Programmatic Access
```javascript
// Get current position from JavaScript
fetch('/api/slam/current_position')
    .then(r => r.json())
    .then(data => {
        console.log(`Position: ${data.position.x}, ${data.position.y}`);
        console.log(`Heading: ${data.position.heading}°`);
        console.log(`Updates: ${data.updates_received}`);
    });
```

```bash
# Get position from command line
curl http://192.168.86.2:8080/api/slam/current_position | jq .position
```

## Next Steps: Waypoint System (Phase A-E)

Once relocation is verified:

### Phase A: Waypoint Backend
- Store waypoints: {name, x, y, z, heading, timestamp}
- Database: SQLite or JSON file

### Phase B: Waypoint API
```
GET /api/waypoints              # List all waypoints
POST /api/waypoints             # Create new waypoint from current position
GET /api/waypoints/{id}         # Get specific waypoint
PUT /api/waypoints/{id}         # Update waypoint
DELETE /api/waypoints/{id}      # Delete waypoint
```

### Phase C: Navigation Logic
```
POST /api/slam/navigate_to
{
    "target_x": 1.5,
    "target_y": 2.0,
    "target_heading": 45.0
}
```
Uses API 1102 (NAVIGATE) with waypoint coordinates

### Phase D: Web UI
- Show current position real-time
- List saved waypoints
- Navigate between waypoints
- Edit waypoint names/coords

### Phase E: Persistence
- Save waypoints across robot restart
- Auto-load on startup
- Resume interrupted navigation

## Troubleshooting

### No Position Updates
```bash
# Check 1: Is map loaded?
ls -lh /home/unitree/room.pcd

# Check 2: Is robot in correct FSM state?
python3 ../test_fsm_state.py  # Should be RUN (500) or LOCK_STAND (501)

# Check 3: Are relocation topics publishing?
python3 check_slam_topics.py  # Should show updates on relocation_odom
```

### Position Not Changing
```bash
# Check 1: Is robot moving?
# Try moving robot with joystick/web controller

# Check 2: Move further/faster
# Small movements may not trigger updates
# Rotate robot - heading change is easier to see

# Check 3: Are you in mapped area?
# Position tracking only works in area you mapped
```

### Position Jumps Around
- Normal during relocation initialization (takes ~10 seconds)
- Keep moving in mapped area
- Try again after 30 seconds

## Status

✅ **READY TO TEST**
- room.pcd map built and verified
- test_relocation.py ready to run
- RobotController tracking position
- Web API endpoint available
- HTML widget available for UI integration

**Next action:** Run `python3 G1_tests/slam/test_relocation.py` and move your robot!

---

**Documentation Files Created:**
- ✅ SLAM_RELOCATION_QUICKSTART.md (5-min guide)
- ✅ SLAM_RELOCATION_TESTING.md (complete guide)
- ✅ SLAM_RELOCATION_IMPLEMENTATION.md (technical)
- ✅ SLAM_POSITION_WIDGET.html (web widget)

**Code Files Modified:**
- ✅ g1_app/core/robot_controller.py (position tracking)
- ✅ g1_app/ui/web_server.py (API endpoint)

**Test Scripts Created:**
- ✅ G1_tests/slam/test_relocation.py (60-sec monitor)
- ✅ G1_tests/slam/check_slam_topics.py (diagnostic)
