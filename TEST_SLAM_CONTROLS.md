# SLAM Control Testing Guide

## What Changed

Added manual SLAM controls to enable/disable the LiDAR sensor.

### New UI Buttons (in LiDAR panel):
- **🗺️ Start SLAM** - Starts SLAM mapping mode, which **enables the LiDAR**
- **⏸️ Stop SLAM** - Stops mapping and saves map (keeps LiDAR active)
- **🛑 Close SLAM** - Closes SLAM completely, **disables the LiDAR**

### How It Works

According to the SDK documentation:
> "Before using, please ensure that the unitree_slam and lidar_driver services of G1 are turned on through the App."

The SLAM service controls the LiDAR. When you start SLAM mapping, it automatically enables the LiDAR driver.

### Testing Steps

1. **Connect to robot** via web UI
2. **Click "🗺️ Start SLAM"** button in LiDAR panel
3. **Wait 3-5 seconds** for LiDAR to initialize
4. **Watch the LiDAR canvas** - should start showing point cloud
5. **Check logs**: `tail -f /tmp/web_server_debug.log | grep -i "slam\|lidar"`

### Expected Behavior

After clicking **Start SLAM**:
- Backend sends API 1801 (START_MAPPING) to `rt/api/slam_operate/request`
- Robot's SLAM service starts mapping mode
- LiDAR driver activates automatically
- Point cloud data starts publishing to `rt/utlidar/cloud_livox_mid360`
- Canvas shows top-down visualization

### Troubleshooting

If LiDAR still doesn't work:
1. Check robot logs: `ssh unitree@192.168.123.164` (password: 123)
2. Verify SLAM service is running: `systemctl status unitree_slam`
3. Check LiDAR hardware: `ping 192.168.123.120`
4. Try Android app - does LiDAR work there?

### API Details

**Service**: `slam_operate` (version 1.0.0.1)

**Start Mapping** (API 1801):
```json
{
  "api_id": 1801,
  "parameter": "{\"data\": {\"slam_type\": \"indoor\"}}"
}
```

**Close SLAM** (API 1901):
```json
{
  "api_id": 1901,
  "parameter": "{\"data\": {}}"
}
```

### Notes

- Only ONE WebRTC connection can be active at a time
- SLAM requires robot in appropriate FSM state (likely LOCK_STAND or RUN)
- LiDAR works best in "static indoor flat scenes with rich features"
- Don't use SLAM while Android app is using navigation
