# G1_6937 - PROVEN WORKING KNOWLEDGE BASE

## SYSTEM STATE (Feb 5, 2026 - VERIFIED)

### Robot Connection
- **Model**: G1 Humanoid (G1_6937)
- **MAC Address**: fc:23:cd:92:60:02 (Unitree prefix)
- **Network IP**: 192.168.86.2 (DHCP assigned, dynamic)
- **Network Interface**: eth1 (192.168.86.0/22 subnet)
- **Discovery Method**: Dynamic MAC-based (via robot_discovery.py)
- **Discovery Time**: ~0.01 seconds (ARP table lookup)

### WebRTC Connection
- **Module**: `unitree_webrtc_connect.webrtc_driver`
- **Connection Method**: `UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=robot_ip)`
- **Status**: ✅ WORKING - tested Feb 5, 2026

### SLAM Operations - PROVEN WORKING

| API ID | Operation | Parameters | Status |
|--------|-----------|------------|--------|
| 1801 | START_MAPPING | `slam_type: "indoor"` | ✅ Working |
| 1802 | END_MAPPING/SAVE | `address: "/home/unitree/*.pcd"` | ✅ Working |
| 1804 | LOAD_MAP | `address, x, y, z, q_x, q_y, q_z, q_w` | ✅ Working |

### SLAM Topics - CRITICAL FOR REAL-TIME VISUALIZATION

| Topic | Use Case | Data | Frequency | Notes |
|-------|----------|------|-----------|-------|
| `rt/unitree/slam_mapping/odom` | **Building Map** | Odometry during SLAM | ~20Hz | Use this when API 1801 is active (mapping) |
| `rt/unitree/slam_relocation/odom` | **Navigating** | Odometry during navigation | ~20Hz | Use this when map is loaded & navigating |
| ~~`rt/unitree/slam_mapping/points`~~ | ❌ WRONG | Point cloud | ❌ Incorrect | **DO NOT USE** - incorrect for map building |

**Key Discovery** (Feb 5, 2026):
- Old implementation used `rt/unitree/slam_mapping/points` (wrong topic)
- Correct topic for building map: `rt/unitree/slam_mapping/odom`
- Correct topic for navigation: `rt/unitree/slam_relocation/odom`
- These topics provide real-time odometry (position/orientation) for 3D visualization

### Navigation Operations - PROVEN WORKING

| API ID | Operation | Parameters | Requirements | Status |
|--------|-----------|------------|--------------|--------|
| 1102 | NAVIGATE_TO | `x, y, z, q_x, q_y, q_z, q_w` | Map loaded (1804) | ✅ Working |

**Navigation Limits:**
- Max distance: 10 meters from current position
- Obstacle detection: 50cm+ height required
- Requires SLAM map to be loaded first

### Motion Control - TESTED

| API ID | Operation | Parameters | Status |
|--------|-----------|------------|--------|
| 7001 | GET_FSM_ID | none | ✅ Tested |
| 7002 | GET_FSM_MODE | none | ✅ Tested |
| 7101 | SET_FSM_ID | `fsm_id: int` | ✅ Tested |

### Actions/Gestures - TESTED

| API ID | Operation | Parameters | Notes | Status |
|--------|-----------|------------|-------|--------|
| 7107 | GET_ACTION_LIST | none | Lists taught actions | ✅ Tested |
| 7108 | EXECUTE_ACTION | `name: string` | Non-blocking execution | ✅ Tested |

### Response Format
```python
# Robot response structure:
response = {
    'type': 'res',
    'topic': 'rt/api/slam_operate/response',
    'data': {
        'header': {...},
        'data': '{"succeed":true,"errorCode":0,"info":"...","data":{}}'
    }
}

# Parse with: parse_slam_response(response)
# Returns: {"succeed": bool, "errorCode": int, "info": str, "data": dict}

# API Request Format (all SLAM/Nav commands):
request = {
    'api_id': int,              # e.g., 1801 for START_MAPPING
    'parameter': {
        'header': {...},
        'data': {...}           # API-specific payload
    }
}

# Response Topic: 'rt/api/slam_operate/response' (for SLAM operations)
# Response Topic: 'rt/api/sport/request' (for motion commands)
```

### Critical Heading/Quaternion Info
**For Navigation with Heading**:
- `heading` in degrees (0-360) or radians (-π to π)
- Quaternion format: `q_x, q_y, q_z, q_w` (x,y,z,w order)
- Conversion: `yaw_to_quaternion(yaw)` in G1_SLAM_IMPLEMENTATION.py
- Formula: 
  ```python
  q_x = 0
  q_y = 0
  q_z = sin(yaw/2)
  q_w = cos(yaw/2)
  ```

**Why Quaternions Matter**:
- Robot orientation in 3D space (not just facing direction)
- Prevents gimbal lock issues
- Standard in robotics (ROS, Unitree SDK)

### Map Storage
- **Location**: `/home/unitree/` on robot
- **Format**: PCD (Point Cloud Data)
- **Example**: `/home/unitree/test_slam_auto.pcd`

### 🔴 CRITICAL DISCOVERY (Feb 5, 2026)

**The Problem**: Old implementation used wrong topic for 3D visualization
- ❌ Old: `rt/unitree/slam_mapping/points` (does NOT work)
- ✅ New: `rt/unitree/slam_mapping/odom` (when mapping)
- ✅ New: `rt/unitree/slam_relocation/odom` (when navigating)

**Why It Matters**:
- `odom` topics provide real-time odometry (position + orientation)
- These are what 3D visualizers need for trajectory tracking
- `points` topic is not the right source for 3D rendering

**For 3D Viewer Implementation**:
1. **During SLAM Mapping** (API 1801 active):
   - Subscribe to: `rt/unitree/slam_mapping/odom`
   - Update viewer with position/heading each message
   - Display accumulated trajectory

2. **During Navigation** (API 1804 loaded, API 1102 executing):
   - Subscribe to: `rt/unitree/slam_relocation/odom`
   - Update viewer with current position/heading
   - Show goal marker + distance to goal
   - Display navigation path

**Testing**: See `test_slam_topics_realtime.py` for verification

### Test Files - CONSOLIDATED IMPLEMENTATIONS
- **Reference Implementation**: `G1_SLAM_IMPLEMENTATION.py` (AUTHORITATIVE)
  - SLAM functions: slam_start_mapping(), slam_save_map(), slam_load_map()
  - Navigation: navigate_to() with obstacle avoidance
  - Motion: get_fsm_mode(), set_fsm_mode()
  - Actions: get_action_list(), execute_action()
- **Main Test**: `g1_tests/slam/simple_slam_test.py` (uses consolidated functions)
- **Original Working**: `g1_tests/test_slam_save_load.py` (Feb 3 baseline)

### Key Functions (from G1_SLAM_IMPLEMENTATION.py)
```python
slam_start_mapping(conn, slam_type="indoor")  # Start SLAM
slam_save_map(conn, map_path: str)            # Save mapping
slam_load_map(conn, map_path: str, pose_x=0, pose_y=0, pose_z=0)  # Load + set pose
parse_slam_response(response: dict) -> dict   # Parse API response
```

## COMPLETED TASKS

✅ **Robot Discovery** - Dynamic MAC-based discovery working
  - Robot found automatically at 192.168.86.2
  - No hardcoded IPs (uses MAC fc:23:cd:92:60:02)
  - Discovery time: 0.01 seconds

✅ **SLAM Mapping** - Complete workflow verified
  - START_MAPPING (API 1801) - working
  - SAVE_MAP (API 1802) - working  
  - LOAD_MAP (API 1804) - working
  - Map created: test_slam_auto.pcd

✅ **Code Consolidation** - Knowledge preserved
  - Consolidated implementation in G1_SLAM_IMPLEMENTATION.py
  - Updated test files to use consolidated functions
  - Removed duplicate/debug test files

## ARCHITECTURE

### WebRTC Flow
```
PC (192.168.86.x) 
  ↓ WebRTC connection (UDP/DTLS)
Robot PC1 (192.168.86.2)
  ↓ Internal DDS
Robot Hardware
```

### SLAM API Message Format
```python
request = {
    "api_id": 1801,  # or 1802, 1804
    "parameter": json.dumps({
        "data": {
            "slam_type": "indoor",  # for 1801
            "address": "/home/unitree/map.pcd",  # for 1802, 1804
            # + pose fields for 1804
        }
    })
}
```

## WAYPOINT SYSTEM - PERSISTENT NAVIGATION

### Data Model
Waypoints are stored persistently per map to enable shutdown/restart navigation:

```json
{
  "map_name": "my_living_room.pcd",
  "created": "2026-02-05T14:30:00Z",
  "modified": "2026-02-05T16:45:00Z",
  "waypoints": [
    {
      "name": "START_POINT",
      "x": 0.0,
      "y": 0.0,
      "z": 0.0,
      "heading": 0.0,
      "description": "Entry point"
    },
    {
      "name": "POINT_A",
      "x": 2.5,
      "y": 1.2,
      "z": 0.0,
      "heading": 45.0,
      "description": "Kitchen area"
    },
    {
      "name": "POINT_B",
      "x": 5.0,
      "y": 3.1,
      "z": 0.0,
      "heading": 90.0,
      "description": "Living room"
    }
  ]
}
```

### Storage Location
- **Path**: `/root/G1/unitree_sdk2/maps/{map_name}_waypoints.json`
- **Lifecycle**: Persistent across shutdown/restart
- **Linked to Map**: One waypoint file per SLAM map

### Navigation Between Waypoints
1. Load map via API 1804 with START waypoint as initial pose
2. Navigate to destination waypoint via API 1102
3. Robot reaches coordinates + rotates to heading
4. Wait for "navigation complete" response
5. Ready for next navigation command

### Session Persistence
- **Current Session**: `/root/G1/unitree_sdk2/sessions/latest_session.json`
- **Tracks**: Current map, current waypoint, robot position estimate
- **On Restart**: Restore session so robot knows which waypoint it's at

## REFERENCE FILES

**DO NOT recreate - use these:**
1. `G1_SLAM_IMPLEMENTATION.py` - Reference implementation (MASTER)
2. `g1_tests/slam/simple_slam_test.py` - Main test using reference
3. `g1_tests/test_slam_save_load.py` - Original Feb 3 baseline
4. `g1_app/core/robot_discovery.py` - Dynamic robot discovery

**OBSOLETE - Do not use:**
- All files in `g1_tests/obsolete/` directory
- Any hardcoded IP address implementations
- Old WebRTC connection files

## NEXT STEPS (NOT DONE YET)

- [ ] Integration test: SLAM + Navigation workflow
- [ ] Real-time pose tracking (subscribe to rt/slam/pose topic)
- [ ] Obstacle avoidance validation with real obstacles
- [ ] Multi-map management
- [ ] Action learning/teaching workflow
- [ ] LiDAR point cloud processing
- [ ] Performance optimization

## HOW TO AVOID REDISCOVERY

**RULE**: Before creating ANY new test/feature:
1. Check `G1_SLAM_IMPLEMENTATION.py` for reference function
2. Check `g1_tests/` folder for existing similar test
3. Reuse functions from consolidated implementation
4. Only create NEW files for genuinely new features (not re-tests)

This prevents knowledge loss and redundant work.
