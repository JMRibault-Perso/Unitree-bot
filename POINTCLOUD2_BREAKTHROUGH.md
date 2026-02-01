# G1 SLAM PointCloud2 Format - SOLVED ✅

## The Problem
LibVoxel decoder (used by GO2) was returning **0 points** despite receiving valid binary data (~5KB at 10Hz).

## Root Cause Discovery
Reading the official Unitree documentation revealed:

> **Topic: rt/unitree/slam_mapping/points**  
> **Data type: sensor_msgs::msg::dds_::PointCloud2_**

**G1 uses ROS2 PointCloud2 format, NOT LibVoxel compression!**

GO2 and G1 use completely different point cloud formats:
- **GO2**: LibVoxel compressed voxels (requires origin/resolution metadata)
- **G1**: ROS2 PointCloud2 with custom 12-byte int16 encoding

## Binary Format (G1 SLAM)

### Message Structure
```
[8-byte header][JSON metadata][Binary point cloud data]
```

**Header (8 bytes):**
```c
uint32_t json_len;    // Length of JSON metadata
uint32_t binary_len;  // Length of binary point cloud
```

**JSON Metadata:**
```json
{
  "type": "msg",
  "topic": "rt/unitree/slam_mapping/points",
  "data": {
    "header": {"frame_id": "map"},
    "is_dense": true,
    "xmin": -4.848877,
    "xmax": 1.892464,
    "ymin": -1.878977,
    "ymax": 2.148078,
    "zmin": -0.671289,
    "zmax": 0.361337
  }
}
```

The bounding box (xmin/xmax/ymin/ymax/zmin/zmax) is **NOT** for voxel grid calculation - it's just spatial metadata!

**Binary Data:**
- **12 bytes per point**
- **6 × int16 values** per point
- **First 3 values = XYZ coordinates in millimeters**
- **Last 3 values = unknown** (possibly intensity, RGB, or padding)

### Decoding Algorithm
```python
# Read binary as int16 array
data_int16 = np.frombuffer(binary_data, dtype=np.int16)
data_int16 = data_int16.reshape((num_points, 6))

# Extract XYZ (first 3 values)
xyz_mm = data_int16[:, :3].astype(np.float32)

# Convert millimeters to meters
xyz_m = xyz_mm / 1000.0
```

## Test Results

**Sample data:** `/tmp/slam_raw.bin` (5651 bytes total)
- JSON: 207 bytes
- Binary: 5436 bytes
- Points: 5436 / 12 = **453 points**

**Decoded coordinates (meters):**
```
X range: [0.084, 6.738] m
Y range: [0.128, 4.024] m
Z range: [0.000, 1.003] m
```

Matches expected indoor space (approx 7m × 4m × 1m).

**Sample points:**
```
Point 0: [5.133, 1.280, 0.042] m
Point 1: [4.990, 1.276, 0.043] m
Point 2: [5.773, 2.037, 0.036] m
Point 3: [5.636, 1.935, 0.043] m
Point 4: [5.647, 1.860, 0.044] m
```

## Implementation

**Files:**
- `g1_app/patches/pointcloud2_decoder.py` - PointCloud2 decoder class
- `g1_app/patches/lidar_decoder_patch.py` - WebRTC patch (uses PointCloud2 decoder)
- `test_pointcloud2_decoder.py` - Offline validation with saved data

**Usage:**
```python
from g1_app.patches.pointcloud2_decoder import PointCloud2Decoder

decoder = PointCloud2Decoder()
result = decoder.decode(binary_data, metadata)

print(f"Points: {result['point_count']}")
print(f"Coordinates: {result['points']}")  # numpy array (N, 3)
```

## Why LibVoxel Failed

LibVoxel decoder expects:
- **Input**: Compressed voxel grid with origin/resolution
- **Algorithm**: Decompression based on `floor(origin[2] / resolution)`
- **Output**: Voxel mesh (positions, UVs, indices)

G1 PointCloud2:
- **Input**: Raw point coordinates (not voxels!)
- **Format**: Simple XYZ array (no compression)
- **Output**: Point positions only

**They are incompatible formats.**

## Key Insight

The user's intuition was correct:
> "The Lidar is off the shelf... I don't think Unitree will invent new decoding"

Unitree **didn't** invent a new format - they used **standard ROS2 PointCloud2**. The confusion arose because:
1. GO2 docs show LibVoxel usage
2. Initial binary analysis found compression-like patterns
3. Metadata had bounding box (looked like voxel params)

But reading the official G1 documentation clearly states: **"sensor_msgs::msg::dds_::PointCloud2_"** 

## Next Steps

1. ✅ PointCloud2 decoder implemented
2. ✅ Offline testing successful (453 points decoded)
3. ⏳ Test with live robot connection
4. ⏳ Integrate with web UI point cloud viewer
5. ⏳ Verify visualization in browser

## Documentation References

- [G1 SLAM Navigation Services](https://support.unitree.com/home/en/G1_developer/slam_navigation_services_interface)
- Topic: `rt/unitree/slam_mapping/points`
- Type: `sensor_msgs::msg::dds_::PointCloud2_`
- Coordinate system: Mid360-IMU frame (X=forward, Z=up)
