# 📋 SLAM Navigation Goals - Complete Clarification (Feb 5, 2026)

## ✅ Goals Are Now Clear

**Old Goal** (Incomplete):  
"Run API 1801, 1802, 1804 to move robot around"

**Actual Goal** (Complete):  
"Build persistent waypoint system so users can map a room, mark points of interest, and navigate between them even after shutdown/restart"

---

## 🎯 Three-Tier Architecture

### Tier 1: SLAM Mapping (Existing - Working ✅)
- User captures 3D map of room
- Stored as `/home/unitree/my_room.pcd`
- APIs: 1801 (start), 1802 (save), 1804 (load)
- Status: **VERIFIED WORKING** Feb 5

### Tier 2: Waypoint System (Planned - New Feature)
- User marks named points in map: "KITCHEN", "BEDROOM", "DOOR"
- Each waypoint has:
  - **Name** (user-friendly identifier)
  - **Coordinates** (x, y, z in map frame)
  - **Heading** (direction robot should face) ⭐ CRITICAL
  - **Description** (optional notes)
- Storage: JSON file per map (survives shutdown)
- Status: **NEEDS IMPLEMENTATION**

### Tier 3: Persistent Navigation (Planned - New Feature)
- User selects: Start waypoint → Destination waypoint → "Navigate"
- Robot:
  1. Loads map
  2. Sets initial pose at start waypoint
  3. Navigates to destination coordinates
  4. Rotates to destination heading
  5. Confirms arrival
- Works even if:
  - App was closed and restarted
  - Robot was shut down
  - Waypoints were modified (added/removed)
- Status: **NEEDS IMPLEMENTATION**

---

## 🔑 Why This Matters - Real Use Cases

### Use Case 1: Cleaning Robot
```
1. Map house floor by floor
2. Mark waypoints: "LIVING_ROOM", "KITCHEN", "BATHROOM", "BEDROOM"
3. Owner can command:
   "Go clean the KITCHEN" → Robot navigates there
   "Return to DOCKING_STATION" → Robot returns
4. Next day: Same commands work (waypoints survived overnight)
```

### Use Case 2: Delivery Robot
```
1. Map building layout
2. Mark: "GROUND_FLOOR", "STAIR_BASE", "SECOND_FLOOR", "OFFICE_JOHN", "OFFICE_SARAH"
3. Schedule deliveries:
   Pick up at GROUND_FLOOR
   → Deliver to OFFICE_JOHN
   → Deliver to OFFICE_SARAH
   → Return to GROUND_FLOOR
4. Robot handles entire route autonomously
```

### Use Case 3: Security Patrol
```
1. Map facility (indoor)
2. Mark patrol checkpoints: "ENTRANCE", "HALLWAY_1", "HALLWAY_2", "SERVER_ROOM", "EXIT"
3. Each night at 10pm: Robot patrols all checkpoints
4. Heading ensures cameras point correct direction
5. Survives nightly shutdown/restart
```

---

## 📦 What Gets Saved/Restored

### Files That Persist
1. **Map files** (already exists)
   - `/home/unitree/my_room.pcd` ← On robot

2. **Waypoint files** (NEW to implement)
   - `/root/G1/unitree_sdk2/maps/my_room_waypoints.json` ← On PC
   - Contains all waypoints for that map

3. **Session file** (NEW to implement)
   - `/root/G1/unitree_sdk2/sessions/latest_session.json` ← On PC
   - Tracks current map, current waypoint, robot position estimate

### Example Waypoint File (NEW)
```json
{
  "map_file": "my_room.pcd",
  "created": "2026-02-05T14:30:00Z",
  "modified": "2026-02-05T16:45:00Z",
  "waypoints": [
    {
      "id": 1,
      "name": "START_POINT",
      "x": 0.0, "y": 0.0, "z": 0.0,
      "heading": 0.0,
      "description": "Entry point / Charging station"
    },
    {
      "id": 2,
      "name": "KITCHEN",
      "x": 2.5, "y": 1.2, "z": 0.0,
      "heading": 45.0,
      "description": "Kitchen area with appliances"
    },
    {
      "id": 3,
      "name": "BEDROOM",
      "x": 5.0, "y": 3.1, "z": 0.0,
      "heading": 90.0,
      "description": "Master bedroom"
    }
  ]
}
```

### Example Session File (NEW)
```json
{
  "timestamp": "2026-02-05T16:45:00Z",
  "loaded_map": "my_room.pcd",
  "robot_estimated_position": {
    "x": 2.5, "y": 1.2, "z": 0.0,
    "heading": 45.0
  },
  "robot_estimated_waypoint": "KITCHEN",
  "last_navigation_goal": "BEDROOM",
  "last_navigation_status": "completed"
}
```

---

## 🔧 Critical APIs to Never Lose

Document these OR THEY'LL BE REDISCOVERED WEEKLY:

### Map Operations
| API | Purpose | Input | Output |
|-----|---------|-------|--------|
| 1801 | Start SLAM | slam_type: "indoor" | {"succeed": bool} |
| 1802 | Save map | address: "/home/unitree/X.pcd" | {"succeed": bool, "info": str} |
| 1804 | Load map + pose | address, x, y, z, q_x, q_y, q_z, q_w | {"succeed": bool, "info": str} |

### Navigation
| API | Purpose | Input | Output |
|-----|---------|-------|--------|
| 1102 | Navigate to goal | x, y, z, q_x, q_y, q_z, q_w | {"succeed": bool} |
| **?** | **Get nav status** | (none) | {distance, heading, status} |

### State Monitoring
| Topic | Purpose | Data | Use |
|-------|---------|------|-----|
| rt/lf/sportmodestate | FSM state | fsm_id, fsm_mode | Verify robot ready |
| rt/lf/odommodestate | Position estimate | x, y, z, heading | Find current waypoint |

**Files to Check for More APIs**:
- `G1_SLAM_IMPLEMENTATION.py` - Working examples
- `KNOWLEDGE_BASE.md` - API reference
- `g1_app/core/command_executor.py` - Payload builders

---

## ⭐ Critical: Heading Support in API 1102

**Question**: Does API 1102 support heading/orientation?

**Why It Matters**: 
- Without it, robot only reaches location but faces random direction
- With it, robot reaches location AND faces correct direction
- Needed for waypoints to be truly useful

**Status**: ⚠️ **NEEDS VERIFICATION**

**See**: `API_1102_HEADING_VERIFICATION.md` for testing procedures

**If Supported** ✅:
```python
# Simple: Include heading in navigate command
navigate_to(x=2.5, y=1.2, z=0.0, heading=45.0)  # Robot faces 45°
```

**If Not Supported** ❌:
```python
# Workaround: Two commands
navigate_to(x=2.5, y=1.2, z=0.0)  # Reach location
rotate_to_heading(heading=45.0)     # Then rotate (need API ID)
```

---

## 📁 File Organization (Keep This Way)

**Do NOT reorganize:**
```
/root/G1/unitree_sdk2/
├── G1_SLAM_IMPLEMENTATION.py           ← Consolidated API functions
├── KNOWLEDGE_BASE.md                   ← Never lose this - API reference
├── GOALS_SLAM_WAYPOINT_SYSTEM.md       ← This detailed plan
├── TEST_PLAN_SLAM_NAVIGATION.md        ← Phases & implementation steps
├── API_1102_HEADING_VERIFICATION.md    ← Heading testing procedure
├── g1_app/
│   ├── core/
│   │   ├── robot_discovery.py
│   │   ├── command_executor.py         ← API payload builders
│   │   ├── robot_controller.py
│   │   └── [NEW] waypoint_manager.py   ← For Phase A
│   ├── ui/
│   │   ├── web_server.py               ← REST endpoints
│   │   └── index.html                  ← Web UI
│   └── ...
├── G1_tests/
│   └── slam/
│       └── simple_slam_test.py         ← Main test
├── maps/                               ← NEW: Store waypoint files
│   └── my_room_waypoints.json
└── sessions/                           ← NEW: Session persistence
    └── latest_session.json
```

---

## ✅ Implementation Checklist

### Phase A: Waypoint Backend (Prerequisite)
- [ ] Create `g1_app/core/waypoint_manager.py`
- [ ] Load waypoint JSON files
- [ ] Save waypoint JSON files
- [ ] Add CRUD methods

### Phase B: Web API (Prerequisite)
- [ ] Add GET `/api/slam/maps/{map}/waypoints` endpoint
- [ ] Add POST `/api/slam/maps/{map}/waypoints` endpoint
- [ ] Add PUT `/api/slam/maps/{map}/waypoints/{name}` endpoint
- [ ] Add DELETE `/api/slam/maps/{map}/waypoints/{name}` endpoint

### Phase C: Navigation Logic (Depends on API 1102 verification)
- [ ] Verify API 1102 heading support (see API_1102_HEADING_VERIFICATION.md)
- [ ] Implement `navigate_waypoint_to_waypoint()` in command_executor.py
- [ ] Add waypoint → coordinate conversion
- [ ] Add heading → quaternion conversion
- [ ] Test on actual robot with actual map

### Phase D: UI (Depends on Phase B)
- [ ] Add waypoint list panel to index.html
- [ ] Add "Mark Current Location" button
- [ ] Add waypoint name & heading inputs
- [ ] Add navigation buttons
- [ ] Add status display

### Phase E: Session Persistence (Depends on Phase B)
- [ ] Create `g1_app/core/session_manager.py`
- [ ] Save session on every state change
- [ ] Restore session on startup
- [ ] Track estimated robot position

---

## 🎓 Learning from This Process

**Why We Almost Lost This**:
1. API calls documented only in test files (not consolidated)
2. Goals confused with implementation (API calls vs. features)
3. No "source of truth" document (rediscovery happens daily)

**How to Prevent It**:
1. **Consolidate**: All functions in ONE reference file (`G1_SLAM_IMPLEMENTATION.py`)
2. **Document Goals**: This file describes what users need, not how APIs work
3. **Preserve Knowledge**: Every new API discovery → KNOWLEDGE_BASE.md

**Rule**: If you don't document it, you'll rediscover it next week.

---

## 📞 Key Decision Point

**Before Starting Implementation**:

⚠️ **Verify API 1102 heading support** (see `API_1102_HEADING_VERIFICATION.md`)

If supported: Straightforward implementation  
If not supported: Need workaround for heading (separate rotation command)

Either way is doable, but the approach changes.

---

## 📊 Success Metrics

When complete:
- ✅ User can create maps and waypoints
- ✅ Waypoints survive shutdown/restart
- ✅ Robot navigates between waypoints with correct heading
- ✅ Multiple maps can coexist
- ✅ User never loses waypoint data

**Bonus**: 
- Navigation routes (sequences of waypoints)
- Automatic patrol patterns
- Collision avoidance improvements
