# G1 SLAM Point Cloud Visualization Guide

## Overview

The G1 robot provides real-time 3D point cloud data during SLAM (Simultaneous Localization and Mapping) operations. This guide explains how to visualize these point clouds in your web browser.

## Key Findings

### Why Raw LiDAR Topics Don't Work

- **rt/utlidar/*** topics return "Invalid Topic" on G1 Air
- G1 uses **SLAM-specific point cloud streaming**, not raw LiDAR like GO2
- Point clouds ONLY available during **active SLAM mapping**

### Point Cloud Architecture

```
┌─────────────────────────────────────────────────────────┐
│ G1 Robot (SLAM System)                                  │
│                                                          │
│  [Livox Mid-360 LiDAR]                                  │
│          ↓                                               │
│  [SLAM Mapping Module]                                  │
│          ↓                                               │
│  rt/unitree/slam_mapping/points (Binary Point Clouds)   │
│  rt/unitree/slam_mapping/odom (Odometry)                │
│  rt/slam_info (Trajectory, Status)                      │
└─────────────────────────────────────────────────────────┘
                    ↓ WebRTC
┌─────────────────────────────────────────────────────────┐
│ Web Controller (Your PC)                                │
│                                                          │
│  [Patched LibVoxel Decoder] ← Bypasses GO2 format check │
│          ↓                                               │
│  [LiDARPointCloudHandler] ← Parses binary to XYZ        │
│          ↓                                               │
│  [Web UI API Endpoint] ← /api/lidar/pointcloud          │
│          ↓                                               │
│  [3D Canvas Viewer] ← Interactive visualization         │
└─────────────────────────────────────────────────────────┘
```

## Decoder Patch

### The Problem

LibVoxel decoder expects GO2 format with `origin` and `resolution` fields:

```python
# LibVoxel decoder (go2_webrtc_connect/unitree_webrtc_connect/lidar/lidar_decoder_libvoxel.py)
data = json.loads(buffer[4:4+json_length])
z_grid_min = math.floor(data["origin"][2] / data["resolution"])  # ❌ KeyError: 'origin'
```

G1 SLAM metadata lacks these fields, causing crashes.

### The Solution

Monkey patch `deal_array_buffer_for_lidar()` to bypass decoding:

```python
# g1_app/patches/lidar_decoder_patch.py
def patched_deal_array_buffer_for_lidar(self, buffer):
    # Extract JSON metadata length (first 4 bytes)
    json_length = int.from_bytes(buffer[:4], byteorder='little')
    
    # Extract JSON metadata
    metadata = json.loads(buffer[4:4+json_length])
    
    # Extract binary point cloud (remaining bytes)
    binary_data = buffer[4+json_length:]
    
    # Return raw data instead of trying to decode
    return {
        'type': 'lidar_pointcloud',
        'binary_data': binary_data,
        'metadata': metadata,
        'size': len(binary_data)
    }

# Apply patch
WebRTCDataChannel.deal_array_buffer_for_lidar = patched_deal_array_buffer_for_lidar
```

Imported in `g1_app/ui/web_server.py` **BEFORE** WebRTC classes load.

## Point Cloud Format

### Binary Structure

```
┌────────────────────────────────┐
│ 4 bytes: JSON length (uint32)  │
├────────────────────────────────┤
│ N bytes: JSON metadata         │
├────────────────────────────────┤
│ M bytes: Binary point cloud    │
│                                │
│ Point format (little-endian):  │
│   [x1, y1, z1, x2, y2, z2, ...]│
│   (float32 array)              │
└────────────────────────────────┘
```

### Parsing Code

```python
import struct

def parse_point_cloud(binary_data: bytes) -> list:
    """Parse SLAM point cloud to XYZ coordinates"""
    num_floats = len(binary_data) // 4
    
    # Must be divisible by 3 for XYZ triplets
    if num_floats % 3 != 0:
        num_floats = (num_floats // 3) * 3
    
    points = []
    for i in range(0, num_floats, 3):
        offset = i * 4
        x, y, z = struct.unpack('<fff', binary_data[offset:offset+12])
        points.append([x, y, z])
    
    return points
```

## Usage

### 1. Start Web Server

```bash
cd /root/G1/unitree_sdk2
python3 -m g1_app.main
```

### 2. Open Point Cloud Viewer

Navigate to: **http://localhost:9000/pointcloud**

### 3. Start SLAM Mapping

Click "Start SLAM Mapping" button in the web UI, or use API:

```bash
curl -X POST http://localhost:9000/api/slam/start \
  -H "Content-Type: application/json" \
  -d '{"slam_type": "indoor"}'
```

### 4. View Point Clouds

- **Rotate**: Click and drag
- **Zoom**: Mouse wheel
- **Reset View**: Click "Reset View" button

Point clouds update at ~10 Hz while SLAM is active.

### 5. Stop Mapping and Save

Click "Stop Mapping" and enter a map name (saved to `/home/unitree/<name>.pcd`):

```bash
curl -X POST http://localhost:9000/api/slam/stop \
  -H "Content-Type: application/json" \
  -d '{"map_name": "my_map.pcd"}'
```

## API Endpoints

### GET /api/lidar/pointcloud

Get latest point cloud data.

**Response:**
```json
{
  "success": true,
  "points": [[x1, y1, z1], [x2, y2, z2], ...],
  "count": 1234
}
```

### POST /api/slam/start

Start SLAM mapping (enables point cloud streaming).

**Request:**
```json
{
  "slam_type": "indoor"  // or "outdoor"
}
```

**Response:**
```json
{
  "success": true,
  "command": {...}
}
```

### POST /api/slam/stop

Stop SLAM mapping and save map.

**Request:**
```json
{
  "map_name": "my_map.pcd"  // Saved to /home/unitree/
}
```

**Response:**
```json
{
  "success": true,
  "map_saved": "/home/unitree/my_map.pcd"
}
```

## Viewer Features

### 3D Controls

- **Mouse Drag**: Rotate view (X/Y axes)
- **Mouse Wheel**: Zoom in/out
- **Reset View**: Return to default camera position

### Color Coding

Points are colored by height (Z coordinate):
- **Blue**: Low elevation
- **Green**: Medium elevation
- **Red**: High elevation

### Statistics

Real-time display of:
- **Point Count**: Total points in current frame
- **FPS**: Rendering frame rate
- **Data Rate**: Point cloud data throughput (KB/s)
- **Last Update**: Timestamp of most recent data

### Status Panel

- **SLAM Status**: Active/Inactive
- **Connection**: Robot connection state
- **Last Update**: Time since last point cloud received
- **Data Rate**: Streaming bandwidth

## Testing

### Test Decoder Patch

```bash
cd /root/G1/unitree_sdk2
python3 test_pointcloud_viewer.py
```

Expected output:
```
📊 Point Cloud #10: 1234 points, 5678 bytes, metadata keys: ['type', 'sec', ...]
   Sample points: [[0.123, -0.456, 0.789], [0.234, -0.567, 0.890], ...]

✅ Point cloud messages received: 200
✅ Latest point count: 1,234
🎉 SUCCESS: Point cloud data flowing without decoder crash!
```

### Test Web UI

1. Start web server
2. Navigate to http://localhost:9000/pointcloud
3. Click "Start SLAM Mapping"
4. Verify point clouds appear within 1-2 seconds
5. Check console for any decoder errors

## Troubleshooting

### No Point Clouds Appearing

**Symptoms:** Point count stays at 0, "No data" message in viewer

**Solutions:**
1. Verify SLAM mapping started: Check "SLAM Status" shows "Active"
2. Check robot connection: Status should show "✅ Connected"
3. Monitor server logs for decoder errors
4. Verify network connection to robot (ping 192.168.86.8)

### Decoder Crashes

**Symptoms:** Server logs show `KeyError: 'origin'` or LibVoxel errors

**Solutions:**
1. Verify patch loaded: Look for "LibVoxel decoder enabled (with G1 SLAM bypass patch)" in logs
2. Check import order: Patch must import BEFORE WebRTC classes
3. Restart web server to reload patches

### Slow/Choppy Visualization

**Symptoms:** FPS drops below 30, laggy controls

**Solutions:**
1. Increase downsampling: Change `points[::10]` to `points[::20]` in robot_controller.py
2. Reduce update frequency: Change `setInterval(100)` to `setInterval(200)` in HTML
3. Clear old points: Implement point cloud history limit

### Map Save Fails

**Symptoms:** "Stop Mapping" returns error

**Solutions:**
1. Check map name is valid: No spaces or special characters
2. Verify robot has write permission to /home/unitree/
3. Ensure SLAM was actively mapping before stopping

## Performance Notes

### Data Throughput

- **Point Cloud Frequency**: ~10 Hz
- **Points Per Frame**: 1,000 - 2,000
- **Binary Size**: 5,400 - 5,700 bytes/frame
- **Bandwidth**: ~50 - 60 KB/s

### Downsampling

To reduce load on web browser:
- Robot sends full point cloud (~1,500 points)
- Handler downsamples to every 10th point (~150 points)
- Configurable in `robot_controller.py`: `points[::10]`

### Memory Usage

- **Browser**: ~10-20 MB for point cloud rendering
- **Server**: Negligible (only stores latest frame)
- **Robot**: SLAM mapping uses ~200 MB RAM

## Advanced Usage

### Custom Point Cloud Processing

```python
from g1_app.core.lidar_handler import LiDARPointCloudHandler

# Create handler
handler = LiDARPointCloudHandler()

# Add custom callback
def my_callback(binary_data: bytes, metadata: dict):
    # Your processing here
    points = parse_point_cloud(binary_data)
    
    # Filter by height
    ground_points = [p for p in points if p[2] < 0.1]
    
    # Detect obstacles
    obstacles = [p for p in points if p[2] > 0.5]
    
    print(f"Ground: {len(ground_points)}, Obstacles: {len(obstacles)}")

handler.add_callback(my_callback)
```

### Export Point Clouds

```python
import json

# Save to JSON
with open('pointcloud.json', 'w') as f:
    json.dump(points, f)

# Save to PLY format (for MeshLab, CloudCompare)
with open('pointcloud.ply', 'w') as f:
    f.write('ply\n')
    f.write('format ascii 1.0\n')
    f.write(f'element vertex {len(points)}\n')
    f.write('property float x\n')
    f.write('property float y\n')
    f.write('property float z\n')
    f.write('end_header\n')
    for x, y, z in points:
        f.write(f'{x} {y} {z}\n')
```

## References

- **Official SDK Docs**: [Unitree SLAM Interface Documentation](https://support.unitree.com/home/en/G1_developer/SLAM_mapping)
- **LibVoxel Decoder**: `/root/G1/go2_webrtc_connect/unitree_webrtc_connect/lidar/lidar_decoder_libvoxel.py`
- **SLAM Topics**: See `test_active_mapping.py` for topic discovery
- **Point Cloud Format**: Reverse-engineered from binary data analysis

## Next Steps

1. **3D Mesh Generation**: Integrate Poisson surface reconstruction
2. **Trajectory Overlay**: Display robot path on point cloud
3. **Real-time SLAM**: Show map building progress
4. **Point Cloud Export**: Save maps in standard formats (PCD, PLY, LAS)
5. **Obstacle Detection**: Highlight obstacles in real-time
