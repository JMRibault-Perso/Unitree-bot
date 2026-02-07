# SLAM Navigation Goals - Updated & Clear

**Status**: Requirements clarified Feb 5, 2026  
**Next Phase**: Waypoint system implementation

---

## ✅ What We Need to Build

### 1. SLAM Mapping (Existing - Working)
- **User Action**: "Start Mapping" → robot walks and records room
- **Result**: Map file saved (e.g., `my_living_room.pcd` in `/home/unitree/`)
- **Status**: ✅ APIs 1801, 1802 verified working
- **Improvement Needed**: Better UI feedback on mapping progress

### 2. Waypoint System (NEW - Core Feature)
- **User Action**: Load map → Click on 3D point cloud → "Save as START_POINT"
- **What's Stored**:
  - Point name (e.g., "START_POINT", "KITCHEN", "OFFICE")
  - X, Y, Z coordinates in map
  - **HEADING** (orientation/direction robot should face)
  - Description (optional)
- **Storage**: JSON file linked to map (survives shutdown/restart)
- **Example**: 
  ```json
  {
    "name": "KITCHEN",
    "x": 2.5, "y": 1.2, "z": 0.0,
    "heading": 45.0,
    "description": "Main kitchen area"
  }
  ```

### 3. Waypoint Navigation (NEW - Core Feature)
- **User Action**: Select source waypoint + destination waypoint → "Navigate"
- **Robot Does**:
  1. Loads map
  2. Sets initial pose at source waypoint
  3. Navigates to destination coordinates
  4. Rotates to destination heading
  5. Announces arrival
- **Status**: API 1102 exists but needs heading support

### 4. Persistence Across Shutdown (NEW - Critical)
- **Scenario 1 (Today)**:
  - Robot at POINT_B
  - Shutdown
  - Restart
  - System knows robot is at POINT_B
  - Can navigate to POINT_A from POINT_B
  
- **Scenario 2 (Complex)**:
  - Robot navigates: START → POINT_A → POINT_B
  - All waypoint coordinates survive shutdown
  - Robot estimates current position using odometry
  - Can resume navigation without knowing exact physical location

- **How**: Session file + waypoint file persists on disk

---

## 🔧 API Knowledge to Preserve (CRITICAL)

We have verified these APIs work. We must NEVER re-discover them:

### SLAM APIs
```python
# API 1801 - Start SLAM Mapping
request = {
    "api_id": 1801,
    "parameter": json.dumps({
        "data": {"slam_type": "indoor"}
    })
}
# Response: {"succeed": true, "errorCode": 0, "info": "Successfully started mapping"}

# API 1802 - Save Map
request = {
    "api_id": 1802,
    "parameter": json.dumps({
        "data": {"address": "/home/unitree/my_room.pcd"}
    })
}
# Response: {"succeed": true, "info": "Save pcd successfully"}

# API 1804 - Load Map + Set Initial Pose
request = {
    "api_id": 1804,
    "parameter": json.dumps({
        "data": {
            "address": "/home/unitree/my_room.pcd",
            "x": 0.0, "y": 0.0, "z": 0.0,
            "q_x": 0.0, "q_y": 0.0, "q_z": 0.0, "q_w": 1.0
        }
    })
}
# Response: {"succeed": true, "info": "Successfully started re-location"}
```

### Navigation API
```python
# API 1102 - Navigate To Goal (with heading via quaternion)
request = {
    "api_id": 1102,
    "parameter": json.dumps({
        "data": {
            "x": 2.5, "y": 1.2, "z": 0.0,
            "q_x": 0.0, "q_y": 0.0, "q_z": 0.383, "q_w": 0.924  # 45° heading
        }
    })
}
# Response: {"succeed": true, "info": "...navigation goal received"}

# Heading Conversion:
# To convert degrees to quaternion:
import math
def heading_to_quaternion(heading_degrees):
    rad = math.radians(heading_degrees)
    return {
        "q_x": 0.0,
        "q_y": 0.0,
        "q_z": math.sin(rad/2),
        "q_w": math.cos(rad/2)
    }
```

### State Monitoring APIs
```python
# Topic: rt/lf/sportmodestate - Get FSM state
# Returns: {"fsm_id": int, "fsm_mode": int, ...}
# Used for: Verifying robot ready for navigation

# Topic: rt/lf/odommodestate - Get robot position estimate
# Returns: {"x": float, "y": float, "z": float, ...}
# Used for: Determining current waypoint, localization
```

---

## 📋 Why Heading Matters

Without heading, waypoint navigation is incomplete:

❌ **Without Heading**:
- Robot reaches (2.5, 1.2) but faces wrong direction
- User must manually rotate robot
- For doorways/entrances, robot might be backwards
- Awkward for camera-based tasks

✅ **With Heading**:
- Robot reaches (2.5, 1.2) AND faces towards (3.0, 2.5)
- Perfect for following corridors
- Doors/entrances handled correctly
- Video camera points right direction
- Professional-looking autonomous behavior

---

## 🗂️ File Organization (PRESERVED)

**Do NOT move files around:**
```
/root/G1/unitree_sdk2/
├── G1_SLAM_IMPLEMENTATION.py          ← AUTHORITATIVE API reference
├── KNOWLEDGE_BASE.md                  ← Updated with API details & waypoint system
├── TEST_PLAN_SLAM_NAVIGATION.md       ← This plan (NEW)
├── SLAM_NAVIGATION_IMPLEMENTATION.md  ← Original Feb 1 implementation
├── README_NAVIGATION_SYSTEM.md        ← Features overview
├── NAVIGATION_QUICK_START.md          ← Quick reference
├── SLAM_MAPS_IMPROVEMENT.md           ← Map detection improvements
├── IMPLEMENTATION_SUMMARY.md          ← What was built
├── g1_app/
│   ├── PROJECT_STATUS.md              ← Phase 1-4 roadmap
│   ├── core/
│   │   ├── robot_discovery.py         ← Dynamic MAC discovery
│   │   ├── command_executor.py        ← API payload builders
│   │   ├── robot_controller.py        ← Main orchestrator
│   │   └── [NEW] waypoint_manager.py  ← Waypoint CRUD
│   ├── ui/
│   │   ├── web_server.py              ← REST API endpoints
│   │   └── index.html                 ← Web interface
│   └── ...
├── g1_tests/
│   ├── slam/
│   │   ├── simple_slam_test.py        ← Main test file
│   │   └── test_complete_slam_workflow.py
│   └── ...
├── maps/                              ← Local map files
│   └── [map_name]_waypoints.json      ← Waypoint storage
└── sessions/                          ← Session persistence
    └── latest_session.json
```

---

## 🎯 Next Implementation Steps

### Step 1: Waypoint Manager Backend
**File**: `g1_app/core/waypoint_manager.py` (create new)
- Load waypoints from JSON
- Save waypoints to JSON
- CRUD operations (add, update, delete, list)

### Step 2: Web API Endpoints
**File**: `g1_app/ui/web_server.py` (modify)
- GET /api/slam/maps/{map_name}/waypoints
- POST /api/slam/maps/{map_name}/waypoints
- PUT /api/slam/maps/{map_name}/waypoints/{name}
- DELETE /api/slam/maps/{map_name}/waypoints/{name}

### Step 3: Waypoint Navigation Command
**File**: `g1_app/core/command_executor.py` (modify)
- Method: `navigate_waypoint_to_waypoint(map, start_wp, dest_wp)`
- Converts waypoint names to coordinates
- Includes heading in navigation request

### Step 4: Web UI
**File**: `g1_app/ui/index.html` (modify)
- Waypoint list panel (table)
- "Mark Current Location" button
- Waypoint name + heading inputs
- Start/destination waypoint selectors
- Navigation button

### Step 5: Session Persistence
**File**: `g1_app/core/session_manager.py` (create new)
- Save/restore session on startup
- Track current map + current waypoint
- Estimate robot position using odometry

---

## ✅ Success Criteria

When complete, users should be able to:

1. ✅ Map a room with SLAM
2. ✅ Mark 5 waypoints (START, POINT_A, B, C, D) with names and headings
3. ✅ Shutdown and restart app
4. ✅ Load same map, see same 5 waypoints
5. ✅ Command: "Go from START to POINT_A" → Robot navigates, arrives at correct heading
6. ✅ Command: "Go from POINT_A to POINT_B" → Robot navigates again
7. ✅ Shutdown robot physically for 30 minutes
8. ✅ Restart robot, load map, all waypoints still there
9. ✅ Robot knows it's "somewhere" and can navigate to any waypoint
10. ✅ No manual re-discovery or reconfiguration needed

---

## 📚 Knowledge Preservation Rule

**Rule**: Every new API or protocol discovery must be documented in:
1. `G1_SLAM_IMPLEMENTATION.py` (code with examples)
2. `KNOWLEDGE_BASE.md` (structured reference)
3. One of the SLAM documentation files

**Why**: Prevents daily rediscovery, enables consistent implementation, survives session restarts.

