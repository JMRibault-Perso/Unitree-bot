# SLAM Map Visualization Investigation - Current Status

## What We've Confirmed

### ✅ Working: Trajectory Visualization
- Live pose tracking from `rt/slam_info` → `currentPose` field
- 2D canvas rendering of robot path
- Color coding by height
- Auto-scaling to fit map bounds
- **This shows WHERE the robot has been, NOT what it saw**

### ❌ Not Working: Room Geometry/Point Cloud

**slam_info fields during mapping:**
```json
{
  "type": "mapping_info",
  "data": {
    "currentPose": {"x": ..., "y": ..., "z": ..., "q_w": ..., ...},
    "pcdName": "",  // EMPTY during mapping
    "address": ""   // EMPTY during mapping
  }
}
```

**Topics available via WebRTC:**
- `rt/slam_info` - Pose + metadata (NO point cloud)
- `rt/slam_key_info` - Task execution feedback
- `rt/api/slam_operate/response` - API responses

**Topics NOT available:**
- `rt/utlidar/cloud_livox_mid360` - Not published on G1 Air
- Any other point cloud or voxel topics

## The Mystery: How Does Android Show the Room?

You confirmed the Android app shows:
> "The map is showing the room live during recording and during motion"

This means Android sees WALLS, OBSTACLES, and ROOM GEOMETRY in real-time - not just a trajectory path.

### Possible Explanations

**1. Video Overlay (Most Likely)**
- SLAM system renders map directly onto H.264 video feed
- Android displays the video, which already has map visualization
- **How to test**: Check if your video feed shows any green/blue overlay or wireframe
- **What it means**: We can't separate map from video without reverse-engineering the decoder

**2. Separate HTTP/WebSocket Endpoint**
- Robot serves map data via HTTP REST API or separate WebSocket
- Android polls/subscribes to this endpoint
- **How to test**: Capture Android network traffic and look for HTTP requests to robot
- **What to look for**: Requests to ports 8000, 8080, 9000 with map/slam/grid/voxel in URL

**3. Binary Data in Datachannel (Unlikely)**
- Point cloud sent as binary WebRTC datachannel messages
- We've been logging these and see ZERO binary LiDAR data (header [2,0])
- **Status**: Already tested, no LiDAR binary messages found

**4. Proprietary Mobile App Protocol**
- Android app uses BLE or special API not documented in SDK
- G1 Air may have different protocol than EDU models
- **How to test**: Decompile Android APK to see what APIs it calls

## Next Steps to Solve This

### Immediate Action: Capture Android Traffic

```bash
# On your PC (while Android app is connected)
sudo tcpdump -i eth1 host 192.168.86.18 -w android_slam_capture.pcap

# In another terminal, use Wireshark
wireshark android_slam_capture.pcap
```

**What to look for:**
- HTTP GET/POST requests for map data
- WebSocket connections beyond WebRTC
- Unusual ports (not 9000 - the WebRTC port)
- Binary protocols with repeating patterns

### Check Video for Overlay

1. Open web controller at http://localhost:9000
2. Connect to robot
3. Start SLAM mapping
4. Look at the video feed - do you see ANY green lines, blue dots, or wireframe overlaid on it?
5. If YES: Map is embedded in video stream (we'd need to decode/extract it)
6. If NO: Map data comes from separate source

### Test HTTP Endpoints

The robot might serve map data via HTTP. Try these URLs while SLAM is active:

```bash
# Try common map endpoints
curl -s http://192.168.86.18:8080/slam/map
curl -s http://192.168.86.18:8080/slam/grid
curl -s http://192.168.86.18:8080/lidar/points
curl -s http://192.168.86.18:9000/slam/stream
curl -s http://192.168.86.18:9000/map/data

# Check if robot has HTTP server
nmap -p 8000-9000 192.168.86.18
```

### Decompile Android App

If network capture doesn't reveal anything, we need to see the app's source code:

```bash
# Download APK from device
adb pull /data/app/com.unitree.explore/base.apk

# Decompile with jadx
jadx -d unitree_explore_decompiled base.apk

# Look for SLAM/map rendering code
grep -r "slam" unitree_explore_decompiled/
grep -r "point.*cloud\|occupancy\|grid\|voxel" unitree_explore_decompiled/
```

## Current Implementation Status

### What Works
- ✅ WebRTC connection to robot
- ✅ SLAM start/stop/close commands
- ✅ Trajectory collection from pose data
- ✅ 2D visualization of robot path
- ✅ Real-time updates (500ms polling)
- ✅ Auto-scaling canvas rendering

### What's Missing
- ❌ Room walls/obstacles visualization
- ❌ LiDAR point cloud data
- ❌ Occupancy grid
- ❌ 3D room geometry

## Recommendations

**Short term** (keep trajectory visualization):
- Use current trajectory view as "where robot has been"
- It's useful for debugging navigation and verifying coverage
- Better than nothing

**Medium term** (find map data source):
1. Capture Android traffic to see what protocol it uses
2. Check if video has embedded overlay
3. Test HTTP endpoints for map data
4. Look for alternative WebSocket connections

**Long term** (if we find the data):
- Integrate point cloud rendering with Three.js
- Show trajectory + room geometry together
- Export to PCD format for offline viewing
- Add AR-style overlay on video feed

## Technical Questions to Answer

1. **Does the Android app video feed show green/blue overlays?**
   - If YES: Map is in video stream
   - If NO: Separate data source

2. **What network traffic does Android generate during SLAM?**
   - HTTP requests?
   - WebSocket beyond WebRTC?
   - UDP packets?

3. **What's in the decompiled Android APK?**
   - Map rendering code
   - API endpoints
   - Binary protocol handlers

4. **Is the "room map" actually real-time?**
   - Or does it only show AFTER stopping mapping?
   - User said "during recording" - so it's real-time

## Conclusion

We've successfully implemented trajectory visualization, but the **room geometry** remains a mystery. The G1 Air appears to use a different protocol than documented in the SDK for map data transmission.

**Most likely theory**: The Android app either:
- Renders map overlay directly on video (embedded in H.264)
- Uses undocumented HTTP/WebSocket endpoint for map updates
- Has special BLE or proprietary protocol not in SDK

Next step: **Capture Android network traffic while SLAM mapping is active** to see what the app is actually doing.
