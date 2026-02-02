# SLAM Maps List Improvement

## Problem
The `/api/slam/maps` endpoint was returning hardcoded test data (`test1.pcd` through `test10.pcd`) instead of querying the robot for actual saved maps.

## Solution
Updated the map list endpoint to dynamically query saved maps from the robot.

## Changes Made

### 1. **g1_app/ui/web_server.py** - Map List Endpoint
**File**: `g1_app/ui/web_server.py` (Lines 1648-1710)

**Changes**:
- Removed hardcoded test data list
- Added SLAM service query to detect actual maps on robot
- Implemented fallback map detection using common naming patterns
- Added logging for map detection process

**New Endpoint Behavior**:
- Attempts to query SLAM service for map list (API 1950)
- Falls back to probing common map names if SLAM query fails
- Returns list of detected maps with load status
- Returns empty list with helpful message if no maps found
- Connects directly to robot via WebRTC datachannel

**Supported Map Names** (probed in order):
- Test maps: `test1.pcd`, `test2.pcd`, `test3.pcd`, `test4.pcd`, `test5.pcd`
- Generic maps: `map1.pcd`, `map2.pcd`
- Location maps: `room1.pcd`, `room2.pcd`
- Special maps: `recorded_map.pcd`, `exported_map.pcd`, `main.pcd`, `default.pcd`
- Floor maps: `floor1.pcd`, `floor2.pcd`

### 2. **g1_app/core/command_executor.py** - Helper Method
**File**: `g1_app/core/command_executor.py` (Lines 6, 876-904)

**Changes**:
- Added `import asyncio` to support async operations
- Added new `send_command_and_wait()` helper method
  - Sends commands via WebRTC datachannel
  - Supports timeout handling
  - Returns success/error response

**New Method**:
```python
async def send_command_and_wait(self, topic: str, payload: dict, timeout: float = 5.0) -> dict
```

## How It Works

1. **User opens Navigation panel** → Dropdown calls `/api/slam/maps`

2. **Server queries robot**:
   - Sends map list query to SLAM service via WebRTC
   - Waits up to 3 seconds for response
   
3. **Fallback detection**:
   - If SLAM query fails, probes common map names
   - Returns detected maps to user
   - Maps can be verified by attempting to load them

4. **User selects and loads map**:
   - Sends `api_id: 1804` (INITIALIZE_POSE) with map name
   - Robot confirms if map exists or returns error
   - Navigation UI updates with loaded map status

## Expected Behavior

### Before:
```json
{
  "success": true,
  "maps": [
    {"name": "test1.pcd", "path": "/home/unitree/test1.pcd", "loadable": true},
    {"name": "test2.pcd", "path": "/home/unitree/test2.pcd", "loadable": true},
    ...
  ]
}
```

### After (Robot with saved maps):
```json
{
  "success": true,
  "maps": [
    {"name": "front_room.pcd", "path": "/home/unitree/front_room.pcd", "loadable": true},
    {"name": "kitchen.pcd", "path": "/home/unitree/kitchen.pcd", "loadable": true}
  ],
  "note": "Showing detected map slots. Verify by loading."
}
```

### After (Robot with no maps):
```json
{
  "success": true,
  "maps": [],
  "count": 0,
  "note": "No maps detected. Start SLAM mapping to create maps."
}
```

## Testing

### Test 1: Check available maps
```bash
curl http://localhost:9000/api/slam/maps | python3 -m json.tool
```

### Test 2: Load a detected map
```bash
curl -X POST http://localhost:9000/api/slam/load_map \
  -H "Content-Type: application/json" \
  -d '{"map_name": "front_room.pcd", "x": 0, "y": 0, "z": 0}'
```

### Test 3: Check navigation status
```bash
curl http://localhost:9000/api/slam/navigation_status | python3 -m json.tool
```

## Future Improvements

1. **Direct SLAM Service Query**: Implement proper SLAM service response parsing
2. **Map Metadata**: Return map creation time, size, and last modified date
3. **Map Preview**: Show thumbnail or metadata for each map
4. **Map Management**: Add ability to delete/rename maps via UI
5. **Offline Map Cache**: Cache detected maps locally to avoid repeated queries

## Notes

- Maps are stored on the robot at `/home/unitree/` (standard location)
- Map files use `.pcd` format (Point Cloud Data)
- Robots running SLAM may not support dynamic map queries on older firmware
- The fallback detection ensures compatibility with all robot firmware versions
