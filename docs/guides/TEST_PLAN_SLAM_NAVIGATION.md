# SLAM Navigation Test Plan - Actual Goals & Requirements

**Date**: February 5, 2026  
**Status**: Requirements Definition Phase  
**Priority**: HIGH - Core functionality for autonomous robot control

---

## 🎯 Actual Goals (NOT just API calls)

### Goal 1: Store Room Maps via SLAM
**What**: Capture complete 3D map of environment using LiDAR + odometry  
**How**: 
- User clicks "Start Mapping" in web UI
- Robot walks around room while SLAM builds point cloud
- User clicks "Stop Mapping" and saves map with name (e.g., "my_living_room")
- Map persists on robot storage (API 1802)

**Success Criteria**:
- ✅ Map saved to `/home/unitree/my_living_room.pcd`
- ✅ Can reload map later (API 1804)
- ✅ Map includes all features/obstacles in room

---

### Goal 2: Mark Waypoints in Map
**What**: Define named points of interest (POI) in the map with exact coordinates and heading  
**How**:
- User loads saved map
- User clicks on 3D point cloud (or enters coordinates manually)
- User assigns name: "START_POINT", "POINT_A", "POINT_B", "CHARGING_STATION"
- System saves: `{name, x, y, z, heading}` → persistent storage
- User can view all waypoints and edit them

**Example Waypoint Data**:
```json
{
  "map_name": "my_living_room.pcd",
  "waypoints": [
    {"name": "START_POINT", "x": 0.0, "y": 0.0, "z": 0.0, "heading": 0.0},
    {"name": "POINT_A", "x": 2.5, "y": 1.2, "z": 0.0, "heading": 45.0},
    {"name": "POINT_B", "x": 5.0, "y": 3.1, "z": 0.0, "heading": 90.0},
    {"name": "CHARGING_STATION", "x": -1.0, "y": 0.5, "z": 0.0, "heading": 180.0}
  ]
}
```

**Success Criteria**:
- ✅ User can add waypoints via UI
- ✅ Waypoints include heading (not just X,Y)
- ✅ Waypoints stored persistently (not lost on reload)
- ✅ User can view/edit/delete waypoints
- ✅ Heading is in degrees (0-360) or radians (-π to π)

---

### Goal 3: Navigate Between Waypoints
**What**: Command robot to travel from one waypoint to another  
**How**:
- User selects map (e.g., "my_living_room")
- User selects start waypoint (e.g., "START_POINT")
- User selects destination (e.g., "POINT_A")
- Robot: loads map → loads start pose → navigates → stops at destination
- Robot arrives with correct heading/orientation

**Example Navigation Sequence**:
```
1. Load map: "my_living_room.pcd"
2. Set initial pose: START_POINT (0, 0, heading=0)
3. Navigate to: POINT_A (2.5, 1.2, heading=45)
   → Robot walks to (2.5, 1.2)
   → Robot rotates to face 45 degrees
   → Stops
4. Later: Navigate to POINT_B (5.0, 3.1, heading=90)
   → Robot walks from current position to (5.0, 3.1)
   → Robot rotates to face 90 degrees
   → Stops
```

**Success Criteria**:
- ✅ Robot reaches correct X,Y coordinates
- ✅ Robot achieves correct heading/orientation
- ✅ Robot can chain multiple waypoint-to-waypoint journeys
- ✅ Works with pause/resume mid-journey

---

### Goal 4: Persistent Navigation After Shutdown
**What**: Robot remembers waypoints and maps even after power cycle  
**How**:
- User navigates robot to POINT_A, saves session
- User powers down robot (or app restarts)
- User powers up robot, loads same map
- System remembers POINT_A location from before
- User can still command: "Go to POINT_A"
- Robot navigates to POINT_A even though it's now at a different physical location

**Example Scenario**:
```
Session 1 (Feb 5, 2pm):
  - Load map: "my_living_room.pcd"
  - Navigate to: POINT_B (5.0, 3.1)
  - Robot is now at POINT_B
  - Shutdown robot
  
Session 2 (Feb 5, 5pm):
  - Power on robot
  - Load same map: "my_living_room.pcd"
  - Waypoints still exist: START_POINT, POINT_A, POINT_B, etc.
  - User commands: "Go to POINT_A"
  - Robot: "I'm currently at POINT_B, navigate to POINT_A"
  - Robot walks from POINT_B → POINT_A
  - Success!
```

**Success Criteria**:
- ✅ Waypoint file survives shutdown/restart
- ✅ Robot can estimate current pose in map (odometry-based)
- ✅ Robot knows which waypoint it's at (or closest to)
- ✅ Can navigate to waypoint from any location
- ✅ Multiple maps + waypoints can coexist

---

## 🔧 Critical APIs to Preserve & Document

### SLAM Operations
| API ID | Name | Purpose | Status |
|--------|------|---------|--------|
| 1801 | START_MAPPING | Begin SLAM capture | ✅ Verified Working |
| 1802 | SAVE_MAP | Save captured map to disk | ✅ Verified Working |
| 1804 | LOAD_MAP | Load map + set initial pose | ✅ Verified Working |

### Navigation Operations
| API ID | Name | Purpose | Status |
|--------|------|---------|--------|
| 1102 | NAVIGATE_TO | Send robot to X,Y coordinates | ⚠️ Documented, needs heading |
| 1805 | ? | Query loaded map status | 🔍 Unknown |
| 1806 | ? | Get robot position in map | 🔍 Unknown |

### State Queries
| Topic | Name | Purpose | Status |
|-------|------|---------|--------|
| rt/lf/sportmodestate | FSM State | Robot operational state | ✅ Verified |
| rt/lf/lowstate | Motor/Battery State | Hardware state | ✅ Verified |
| rt/lf/odommodestate | Odometry | Robot position in map | ⚠️ Needs verification |

---

## 📊 Implementation Phases

### Phase A: Waypoint Storage System (Backend)
**Files to Create/Modify**:
- `g1_app/core/waypoint_manager.py` (NEW)
  - Load/save waypoints from JSON/file
  - CRUD operations (Create, Read, Update, Delete)
  - Associate waypoints with maps
  
- `g1_app/ui/web_server.py` (MODIFY)
  - New endpoints:
    - `GET /api/slam/maps/{map_name}/waypoints` - List waypoints
    - `POST /api/slam/maps/{map_name}/waypoints` - Add waypoint
    - `PUT /api/slam/maps/{map_name}/waypoints/{name}` - Update waypoint
    - `DELETE /api/slam/maps/{map_name}/waypoints/{name}` - Delete waypoint

**Data Storage**:
- File location: `/root/G1/unitree_sdk2/maps/{map_name}_waypoints.json`
- Format:
  ```json
  {
    "map_name": "my_living_room.pcd",
    "created": "2026-02-05T14:30:00Z",
    "modified": "2026-02-05T16:45:00Z",
    "waypoints": [
      {"name": "START_POINT", "x": 0.0, "y": 0.0, "z": 0.0, "heading": 0.0},
      {"name": "POINT_A", "x": 2.5, "y": 1.2, "z": 0.0, "heading": 45.0}
    ]
  }
  ```

### Phase B: Waypoint UI (Frontend)
**Files to Modify**:
- `g1_app/ui/index.html` (MODIFY)
  - Add waypoint panel with:
    - List of waypoints (editable table)
    - "Mark Current Location" button
    - Waypoint name input
    - Heading input (degrees or visual dial)
    - Delete waypoint button

**User Interaction**:
1. Load map → Show waypoints in panel
2. Click "Mark Current Location" → Robot's current X,Y captured
3. Name it + set heading → Saved to waypoint list
4. Select start + destination waypoints → Click "Navigate"

### Phase C: Waypoint Navigation (Logic)
**Files to Modify**:
- `g1_app/core/command_executor.py` (MODIFY)
  - New method: `navigate_between_waypoints(map_name, start_wp, dest_wp)`
  - Logic:
    1. Load map with start waypoint as initial pose
    2. Navigate to destination waypoint coordinates
    3. Rotate to destination heading
    4. Confirm arrival

- `g1_app/core/robot_controller.py` (MODIFY)
  - Add state tracking: `current_waypoint`
  - Add method: `find_nearest_waypoint()` on startup
  - Add method: `navigate_waypoint_to_waypoint()`

### Phase D: Persistence & Session Management
**Files to Create**:
- `g1_app/core/session_manager.py` (NEW)
  - Save session state (current map, current waypoint, etc.)
  - Restore session on restart
  - Track robot position in map over time

**Data Files**:
- Session: `/root/G1/unitree_sdk2/sessions/latest_session.json`
  ```json
  {
    "timestamp": "2026-02-05T16:45:00Z",
    "loaded_map": "my_living_room.pcd",
    "robot_position": {"x": 2.5, "y": 1.2, "z": 0.0, "heading": 45.0},
    "estimated_waypoint": "POINT_A",
    "last_command": "navigate_to_waypoint"
  }
  ```

---

## ✅ Test Cases (When Ready)

### Test 1.1: Create Map & Waypoints
```
Input: User maps living room, marks 3 waypoints
Expected:
  ✓ Map file saved to /home/unitree/my_living_room.pcd
  ✓ Waypoint file created with 3 points
  ✓ Each waypoint has name, x, y, heading
```

### Test 1.2: Navigate Between Waypoints
```
Input: Navigate START_POINT → POINT_A → POINT_B → START_POINT
Expected:
  ✓ Robot reaches each coordinate
  ✓ Robot achieves heading at each stop
  ✓ Path visible in 3D viewer
```

### Test 1.3: Shutdown & Restart Navigation
```
Input: Navigate to POINT_A, shutdown, restart, navigate to POINT_B
Expected:
  ✓ Waypoints still exist after restart
  ✓ Robot can navigate to POINT_B from anywhere
  ✓ Odometry updates during navigation
```

### Test 1.4: Real-World Scenario
```
Input: Robot room delivery
  1. Start at POINT_A (kitchen)
  2. Navigate to POINT_B (office)
  3. Wait 30 seconds
  4. Navigate to POINT_C (bedroom)
  5. Wait 30 seconds
  6. Return to POINT_A
Expected:
  ✓ Robot completes route without operator input
  ✓ Robot maintains accuracy across multiple legs
  ✓ No drift over time
```

---

## 🔑 Why This Matters

**Current State**: We have raw API calls that move robot from A to B  
**What's Missing**: Waypoints that survive shutdown/restart, semantic meaning ("kitchen", "office"), heading awareness

**Real-World Use Cases**:
- 🏠 Home delivery: "Go to living room, then bedroom"
- 🏢 Office patrol: "Visit conference room, bathroom, kitchen"
- 🏭 Warehouse: "Load from dock, deliver to station A, return"
- 🎓 School: "Tour rooms in fixed sequence"

All of these require **persistent waypoints** + **reliable navigation** + **heading awareness**

---

## 📝 Knowledge Preservation

**Critical**: Document all API payloads, response formats, and state transitions  
**Where**: `KNOWLEDGE_BASE.md` (continuously updated)  
**Discipline**: Every API call gets logged with:
- Request format
- Response format
- Success/failure conditions
- Example with real robot response

This prevents rediscovery and ensures consistency across sessions.

---

## 🚀 Next Steps

1. **Approval**: Confirm these are the actual goals
2. **API Review**: Verify all needed APIs work (esp. 1102 with heading)
3. **Design**: Create data models for waypoints
4. **Implementation**: Start with Phase A (backend storage)
5. **Testing**: Test each phase independently before integration
