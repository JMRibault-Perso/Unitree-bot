# API 1102 Navigation - Heading Support Verification Needed

**API ID**: 1102  
**Name**: NAVIGATE_TO  
**Status**: ⚠️ Needs verification with heading  
**Date**: February 5, 2026

---

## Current Implementation

```python
async def navigate_to(conn, x: float, y: float, z: float, yaw: float = 0.0):
    """
    Navigate robot to target coordinates with heading.
    
    Args:
        conn: WebRTC connection
        x, y, z: Target coordinates (meters)
        yaw: Target heading in radians (or degrees - TBD)
    
    Returns:
        dict: Response with success/error
    """
    # Convert yaw to quaternion
    q_z = math.sin(yaw / 2)
    q_w = math.cos(yaw / 2)
    
    request = {
        "api_id": 1102,
        "parameter": json.dumps({
            "data": {
                "x": x, "y": y, "z": z,
                "q_x": 0.0, "q_y": 0.0, "q_z": q_z, "q_w": q_w
            }
        })
    }
    
    response = await conn.send_request(request)
    return parse_slam_response(response)
```

---

## Critical Questions to Test

### Question 1: Does API 1102 accept heading/quaternion?
**Test Command**:
```bash
# Test navigation with heading
curl -X POST http://localhost:9000/api/slam/navigate_to \
  -H "Content-Type: application/json" \
  -d '{
    "x": 2.0,
    "y": 1.0,
    "z": 0.0,
    "heading_degrees": 90.0
  }'

# Expected Response:
# {"success": true, "goal": {"x": 2, "y": 1, "heading": 90}}
```

### Question 2: What format does heading need?
**Options to test**:
- A) Radians: -π to π
- B) Degrees: 0-360 or -180 to 180
- C) Quaternion (x,y,z,w): Raw quaternion values
- D) Robot accepts all three and auto-converts

### Question 3: Does robot rotate at destination?
**Observation**:
- Send robot to (2, 1) with heading 90°
- Robot reaches (2, 1)
- **CRITICAL**: Does robot then rotate to face 90°? Or just arrive at location?
- Watch robot's final orientation to confirm

### Question 4: What's the response format?
**Need to capture**:
```python
response = {
    "succeed": true/false,
    "errorCode": 0,
    "info": "... message ...",
    "data": {
        # What does data contain?
        # Goal accepted? Current progress? ETA?
    }
}
```

---

## How to Test

### Test 1: Basic Navigation with Heading (if we have a map)
```bash
cd /root/G1/unitree_sdk2

# Make sure web server running
python3 -m g1_app.ui.web_server &

# Wait for server startup
sleep 3

# Test endpoint
curl -X POST http://localhost:9000/api/slam/navigate_to \
  -H "Content-Type: application/json" \
  -d '{"x": 1.0, "y": 0.5, "z": 0.0, "heading_degrees": 45.0}' \
  | python3 -m json.tool

# Watch robot - does it:
# 1. Walk to (1.0, 0.5)? ✓
# 2. Rotate to face 45°? ✓ or ✗
```

### Test 2: Navigation Status Feedback
```bash
# During navigation, query status
curl http://localhost:9000/api/slam/navigation_status | python3 -m json.tool

# Expected fields:
# - goal_x, goal_y, goal_heading
# - current_x, current_y, current_heading
# - distance_to_goal
# - status (navigating/paused/completed)
```

### Test 3: Multiple Waypoint Chain
```python
# Test sequence:
# 1. Start at (0, 0) facing 0°
# 2. Navigate to (2, 0) facing 90°
# 3. Navigate to (2, 2) facing 180°
# 4. Navigate to (0, 2) facing 270°
# 5. Return to (0, 0) facing 0°

waypoints = [
    (0, 0, 0),      # Start
    (2, 0, 90),     # Right, facing right
    (2, 2, 180),    # Up, facing up (away from start)
    (0, 2, 270),    # Left, facing left (toward start)
    (0, 0, 0),      # Back to start, facing original direction
]

for i, (x, y, heading) in enumerate(waypoints):
    print(f"Step {i+1}: Navigate to ({x}, {y}) heading {heading}°")
    # Send navigation command
    # Wait for completion
    # Verify final position and orientation
    # Check if waypoint file survives this sequence
```

---

## Data to Capture from Real Robot

When testing, capture this data:

```python
test_result = {
    "timestamp": "2026-02-05T15:30:00Z",
    "test_name": "API_1102_heading_support",
    "input": {
        "x": 2.0, "y": 1.0, "z": 0.0,
        "heading_degrees": 45.0
    },
    "response": {
        # Copy actual response from robot
    },
    "observations": {
        "robot_reached_target": True,  # Did it reach (2.0, 1.0)?
        "robot_rotated_to_heading": True,  # Did it rotate to 45°?
        "final_position": {"x": 2.01, "y": 1.02, "z": 0.0},  # Measured
        "final_heading_degrees": 45.2  # Measured
    },
    "notes": "Robot behavior observations..."
}
```

---

## If Heading NOT Supported

If API 1102 doesn't support heading (just X,Y,Z):

**Workaround Option 1**: Use separate rotation command
```python
async def navigate_with_heading(conn, x, y, z, heading):
    # Step 1: Navigate to coordinates (no heading)
    await navigate_to(conn, x, y, z)
    
    # Step 2: Wait for arrival (poll status)
    while True:
        status = await get_navigation_status(conn)
        if status["completed"]:
            break
        await asyncio.sleep(0.1)
    
    # Step 3: Send separate rotation command (API ???)
    await rotate_to_heading(conn, heading)  # Need to find this API
```

**Workaround Option 2**: Manual rotation via motion control
```python
# Use API 7101 (SET_FSM) to enter rotation state
# Send turn velocity to rotate robot
# Monitor compass until facing correct direction
```

**Impact on Waypoint System**: Would need two commands per waypoint:
1. Navigate to (x, y)
2. Rotate to heading

Less elegant but still functional.

---

## Success Condition

✅ **Confirmed**: API 1102 accepts heading and robot rotates at destination  
⚠️ **Workaround**: Robot doesn't rotate; we'll use separate rotation command  
❌ **Problem**: No way to specify heading; waypoint system incomplete

---

## Next Action Required

Run Test 1 above and report:
1. Does robot reach target coordinates? (check position logs)
2. Does robot rotate to target heading? (visual inspection)
3. What is the actual response format from API 1102?
4. Does navigation status endpoint report heading?

This will determine if heading support is native or needs workaround.

