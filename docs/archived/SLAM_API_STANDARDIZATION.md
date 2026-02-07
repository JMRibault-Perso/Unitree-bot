# SLAM API Standardization - Complete

## Overview
All SLAM code across the workspace now uses a **consistent, unified API calling pattern**. This ensures:
- ✅ No more mixed patterns (raw API calls vs wrapper functions)
- ✅ No more blocking input() calls breaking WebRTC connections
- ✅ All files use the proper `RobotTestConnection` wrapper
- ✅ All files use standardized `SLAM_API` constants
- ✅ Consistent response validation with `check_slam_response()`

## Standard Pattern

### ✅ CORRECT - All SLAM code now follows this pattern:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response

async def main():
    async with RobotTestConnection() as robot:
        # API calls use: robot.send_slam_request(SLAM_API['API_NAME'], params)
        response = await robot.send_slam_request(SLAM_API['START_MAPPING'], {"slam_type": "indoor"})
        check_slam_response(response, "Start Mapping")  # Validate response
        
        # Non-blocking delays instead of input()
        for i in range(60, 0, -10):
            await asyncio.sleep(10)
```

### ❌ WRONG - Old patterns (now removed):

```python
# WRONG: Raw WebRTC calls
conn.datachannel.pub_sub.publish_request_new("rt/api/slam_operate/request", payload)

# WRONG: Manual API ID wrapping
payload = {"api_id": 1801, "parameter": json.dumps({"data": {...}})}

# WRONG: Mixing implementations
from G1_SLAM_IMPLEMENTATION import slam_start_mapping  # Don't mix this with raw API calls

# WRONG: Blocking I/O
input("Press Enter...")  # Breaks WebRTC connection!
```

## Files Standardized

### Core SLAM Tests (✅ All standardized)
| File | Status | Key Change |
|------|--------|-----------|
| `G1_tests/slam/simple_map_build.py` | ✅ | Reference implementation - no changes needed |
| `G1_tests/slam/simple_slam_test.py` | ✅ | Replaced G1_SLAM_IMPLEMENTATION + raw calls with RobotTestConnection |
| `G1_tests/slam/start_mapping.py` | ✅ | Already using RobotTestConnection |
| `G1_tests/slam/save_map.py` | ✅ | Already using RobotTestConnection |
| `G1_tests/slam/load_map.py` | ✅ | Already using RobotTestConnection |
| `G1_tests/slam/stop_slam_v2.py` | ✅ | Already using RobotTestConnection |
| `G1_tests/slam/cancel_navigation_v2.py` | ✅ | Already using RobotTestConnection |
| `G1_tests/slam/test_navigation_v2.py` | ✅ | Already using RobotTestConnection |

### Workspace-level SLAM Tests (✅ All standardized)
| File | Status | Key Changes |
|------|--------|------------|
| `build_room_map.py` | ✅ | Replaced raw WebRTC calls with RobotTestConnection |
| `test_map_build_with_joystick.py` | ✅ | Removed `input()`, added 60-sec auto-timer |
| `test_api_1102_heading.py` | ✅ | Removed `input()`, added asyncio.sleep() delays |
| `test_complete_slam_workflow.py` | ✅ | Removed all `input()` calls, added auto-timers |

## SLAM_API Constants

All files use these standardized constants from `robot_test_helpers.py`:

```python
SLAM_API = {
    'START_MAPPING': 1801,      # Begin LiDAR capture
    'END_MAPPING': 1802,        # Stop mapping and save
    'STOP_MAPPING': 1802,       # Alias for END_MAPPING
    'SAVE_MAP': 1802,           # Alias for END_MAPPING
    'LOAD_MAP': 1804,           # Load map for navigation
    'INITIALIZE_POSE': 1804,    # Alias for LOAD_MAP
    'NAVIGATE': 1102,           # Navigate to target pose
    'PAUSE_NAV': 1201,          # Pause navigation
    'RESUME_NAV': 1202,         # Resume navigation
    'CLOSE_SLAM': 1901,         # Close SLAM system
}
```

## API Calling Method

**All SLAM code now uses this single method:**

```python
response = await robot.send_slam_request(SLAM_API['KEY'], parameters)
check_slam_response(response, "Operation Name")
```

### Parameter Format Examples:

```python
# START_MAPPING
await robot.send_slam_request(SLAM_API['START_MAPPING'], {"slam_type": "indoor"})

# LOAD_MAP
await robot.send_slam_request(SLAM_API['LOAD_MAP'], {
    "x": 0.0, "y": 0.0, "z": 0.0,
    "q_x": 0.0, "q_y": 0.0, "q_z": 0.0, "q_w": 1.0,
    "address": "/home/unitree/room.pcd"
})

# NAVIGATE
await robot.send_slam_request(SLAM_API['NAVIGATE'], {
    "targetPose": {
        "x": 1.0, "y": 0.5, "z": 0.0,
        "q_x": 0.0, "q_y": 0.0, "q_z": 0.707, "q_w": 0.707
    },
    "mode": 1
})
```

## Testing Workflow

All tests now follow this non-blocking pattern:

```python
async def main():
    async with RobotTestConnection() as robot:
        # Phase 1
        response = await robot.send_slam_request(SLAM_API['START_MAPPING'], {...})
        check_slam_response(response, "Operation")
        
        # Phase 2: Auto-timer instead of input()
        for i in range(60, 0, -10):
            print(f"⏱️  {i} seconds remaining...", flush=True)
            await asyncio.sleep(10)  # Non-blocking!
        
        # Phase 3
        response = await robot.send_slam_request(SLAM_API['NEXT_API'], {...})
        check_slam_response(response, "Operation")
```

## Key Improvements

### 1. No More Blocking I/O
- ❌ `input()` - REMOVED (was breaking WebRTC)
- ✅ `await asyncio.sleep()` - ADDED (non-blocking)

### 2. Unified API Access
- ❌ Raw `conn.datachannel.pub_sub.publish_request_new()` - REMOVED
- ✅ `robot.send_slam_request(SLAM_API[key], params)` - STANDARDIZED

### 3. Consistent Response Handling
- ✅ All responses validated with `check_slam_response()`
- ✅ All parameters use same naming conventions
- ✅ All async/await patterns are identical

### 4. Connection Management
- ✅ All use `async with RobotTestConnection() as robot:` context manager
- ✅ Automatic cleanup on exit (even if error occurs)
- ✅ No manual connect/disconnect boilerplate

## Verification

Run any of these to verify standardization:

```bash
# Reference implementation (guaranteed to work)
cd /root/G1/unitree_sdk2/G1_tests/slam && python3 simple_map_build.py

# Other standardized files
python3 simple_slam_test.py
python3 start_mapping.py
python3 save_map.py
python3 load_map.py
python3 stop_slam_v2.py
cd /root/G1/unitree_sdk2 && python3 build_room_map.py
```

## Migration Guide (if new code needed)

When writing NEW SLAM code, use this template:

```python
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response

async def main():
    async with RobotTestConnection() as robot:
        # Your SLAM code here - always use:
        # 1. robot.send_slam_request(SLAM_API['KEY'], params)
        # 2. check_slam_response(response, "Description")
        # 3. await asyncio.sleep() for delays (never input())
        pass

if __name__ == '__main__':
    asyncio.run(main())
```

## Status: ✅ COMPLETE

All SLAM code in the workspace now uses:
- ✅ Unified `RobotTestConnection` wrapper
- ✅ Standardized `SLAM_API` constants
- ✅ Consistent `robot.send_slam_request()` method
- ✅ Unified response validation with `check_slam_response()`
- ✅ Non-blocking async/await patterns
- ✅ No mixing of implementations
- ✅ No blocking I/O breaking WebRTC

**Result: Ready for reliable SLAM testing and waypoint navigation implementation.**
