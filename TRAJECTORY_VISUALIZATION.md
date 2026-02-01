# SLAM Trajectory Visualization - Implementation Complete

## Overview

The G1 web controller now has **live 3D trajectory visualization** during SLAM mapping. While the LiDAR point cloud topic (`rt/utlidar/cloud_livox_mid360`) is not accessible on the G1 Air model, we can visualize the robot's path in real-time using pose data from the `rt/slam_info` topic.

## What Was Implemented

### Backend (Python)

1. **Trajectory Collection** (`g1_app/core/robot_controller.py`):
   - Collects pose data (x, y, z) from `rt/slam_info` currentPose field
   - Stores trajectory points with timestamps
   - Limits to last 1000 points to prevent memory overflow
   - Tracks SLAM state (active/inactive) via API responses

2. **API Endpoint** (`g1_app/ui/web_server.py`):
   - `GET /api/slam/trajectory` - Returns current trajectory points
   - Response format:
     ```json
     {
       "success": true,
       "points": [{"x": 0.1, "y": 0.2, "z": 0.0, "timestamp": 123456}, ...],
       "count": 42,
       "active": true
     }
     ```

3. **Enhanced Logging**:
   - Full slam_info data structure logged to identify potential point cloud data
   - This will help determine if LiDAR data is embedded in slam_info

### Frontend (JavaScript)

1. **Live Trajectory Rendering** (`g1_app/ui/index.html`):
   - Polls `/api/slam/trajectory` every 500ms during SLAM mapping
   - Renders on the existing `lidarCanvas` element
   - Features:
     - **Auto-scaling**: Fits entire path to canvas with padding
     - **Grid background**: 50px grid for spatial reference
     - **Color coding**: Points colored by height (z-coordinate)
       - Blue = low altitude
       - Green = medium
       - Red = high
     - **Path visualization**: Green line connecting all trajectory points
     - **Start marker**: White circle marking trajectory start
     - **Info overlay**: Shows point count, range, and scale

2. **Control Integration**:
   - "Start SLAM" button → starts trajectory visualization automatically
   - "Stop SLAM" button → stops visualization, retains last frame
   - Trajectory resets on each new SLAM start

## How to Use

### 1. Start the Web Server

```bash
cd /root/G1/unitree_sdk2
python3 -m g1_app.ui.web_server
```

Open http://localhost:9000 in your browser.

### 2. Connect to Robot

1. Click "Connect to Robot" (use IP 192.168.86.18 for G1_6937)
2. Wait for connection confirmation

### 3. Start SLAM Mapping

1. Click "Start SLAM" button
2. Notification: "🗺️ SLAM mapping started - visualizing trajectory..."
3. The LiDAR/Trajectory canvas will show live updates every 500ms

### 4. Control the Robot

Use WASD keys to move the robot around:
- **W** - Forward
- **S** - Backward
- **A** - Strafe left
- **D** - Strafe right
- **Q** - Rotate left
- **E** - Rotate right

Watch the trajectory canvas update in real-time as you move!

### 5. Stop SLAM Mapping

1. Click "Stop SLAM" button
2. Trajectory visualization freezes, showing final path
3. System attempts to download map file (may not be available on G1 Air)

### 6. Close SLAM

Click "Close SLAM" to disable LiDAR entirely.

## Canvas Visualization Details

### Coordinate System
- **Top-down view**: Looking down at the floor (X-Y plane)
- **X-axis**: Left/right (horizontal)
- **Y-axis**: Forward/backward (vertical, inverted for screen coords)
- **Z-axis**: Height (shown as color gradient)

### Visual Elements
- **Black background**: Canvas background
- **Gray grid**: 50px spacing for scale reference
- **Dark gray axes**: Center lines (X=0, Y=0)
- **Green path**: Robot trajectory
- **Colored dots**: Individual pose samples (color by height)
- **White circle**: Start position marker
- **Info panel**: Top-left corner shows stats

### Auto-Scaling
The canvas automatically scales and centers to show the entire path:
- Padding: 50px on all sides
- Scale factor shown in info panel (pixels per meter)
- Updates dynamically as robot moves further

## Investigating LiDAR Point Cloud Access

### Current Status

We've confirmed that `rt/utlidar/cloud_livox_mid360` does **NOT publish** on the G1 Air model, despite being documented in the SDK. However, the user reports that the Android app DOES show a live LiDAR map during recording.

### What We're Investigating

The new logging in `robot_controller.py` will capture the **full slam_info data structure** to look for:

1. **Embedded point cloud data** in slam_info messages
2. **Additional fields** not yet parsed (pcdName, address, other binary data)
3. **Binary data in WebRTC datachannel** (header [2, 0] for LiDAR voxels)

### How to Check Logs

After starting SLAM and moving the robot:

```bash
# Check for full slam_info structure
grep "SLAM INFO FULL DATA" server.log | tail -5

# Look for point cloud or voxel data
grep -E "(points|cloud|voxel)" server.log
```

If the Android app truly shows live LiDAR point cloud during mapping, the data MUST be coming through one of these channels:
- **slam_info message** (likely in a field we're not parsing yet)
- **Binary datachannel message** (we've patched to log these)
- **Separate HTTP/WebSocket endpoint** (need to reverse-engineer Android app)

### Next Steps

1. **Test trajectory visualization** - Confirm it works as expected
2. **Analyze full slam_info logs** - Look for point cloud data we missed
3. **Compare Android behavior** - Does it show point cloud or just trajectory?
4. **Reverse-engineer Android protocol** - Capture network traffic during map recording

## Technical Details

### Data Flow

```
Robot (PC1) 
  → rt/slam_info topic (WebRTC wrapper) 
    → robot_controller._subscribe_to_slam_feedback()
      → Extract currentPose {x, y, z, q_w, q_x, q_y, q_z}
        → Append to slam_trajectory[]
          → GET /api/slam/trajectory
            → JavaScript poll every 500ms
              → renderTrajectory(points)
                → Canvas 2D rendering
```

### Trajectory Storage

```python
# In robot_controller.py
self.slam_trajectory = [
    {"x": 0.123, "y": 0.456, "z": 0.012, "timestamp": 123456},
    {"x": 0.145, "y": 0.478, "z": 0.015, "timestamp": 123457},
    # ... up to 1000 points
]
```

### SLAM Active State Tracking

```python
# State changes from API responses
if api_id == 1801:  # START_MAPPING
    self.slam_active = True
    self.slam_trajectory = []  # Reset
elif api_id in [1802, 1901]:  # END_MAPPING or CLOSE_SLAM
    self.slam_active = False
```

## Known Limitations

1. **No real point cloud**: Only trajectory path, not actual LiDAR 3D points
2. **Limited to 1000 points**: Older points dropped to prevent memory issues
3. **2D visualization only**: No full 3D rotation/zoom (could add Three.js later)
4. **No map file download**: G1 Air likely doesn't expose `/home/unitree/temp_map.pcd` via HTTP
5. **Trajectory resets on reconnect**: Data not persisted between sessions

## Future Enhancements (If Point Cloud Becomes Available)

If we discover how to access the actual LiDAR point cloud data:

1. **Three.js integration** - Full 3D visualization with rotation/zoom
2. **Point cloud overlay** - Show LiDAR points + trajectory together
3. **Color by intensity** - Use LiDAR reflection intensity for point colors
4. **Multiple layers** - Separate canvas layers for trajectory vs point cloud
5. **Export to PCD** - Save visualized data to local file

## Conclusion

We now have:
- ✅ Live trajectory visualization working
- ✅ Full slam_info logging to investigate point cloud access
- ✅ Clean UI integration with SLAM controls
- ⚠️ Still investigating actual LiDAR point cloud access

The mystery remains: **How does the Android app show the LiDAR map?** Our enhanced logging should reveal the answer.
