# Sensor Tests

LiDAR, cameras, IMU, and telemetry monitoring tests.

## 🗂️ Available Tests

### LiDAR
- `test_lidar_realtime.py` - Live point cloud visualization
- `test_lidar_topics.py` - Discover and monitor LiDAR topics
- `monitor_lidar.py` - Continuous LiDAR data monitoring

### Cameras
- `test_video_stream.py` - WebRTC video stream test
- `monitor_cameras.py` - Multi-camera feed monitoring

### Telemetry
- `listen_all_topics.py` - Monitor all robot topics
- `listen_telemetry.py` - Focused telemetry logging
- `test_imu.py` - IMU data validation

### Audio
- `test_audio_vui.py` - TTS and speech recognition
- `test_led_control.py` - LED pattern control

## 📡 Common Topics

### LiDAR Topics
- `rt/utlidar/cloud_livox_mid360` - Primary LiDAR point cloud
- `rt/utlidar/imu` - LiDAR IMU data
- `rt/utlidar/cloud` - Processed point cloud

### State Topics  
- `rt/lf/sportmodestate` - Robot state, FSM, odometry
- `rt/lf/bmsstate` - Battery management
- `rt/lf/lowstate` - Low-level motor states

### Video Topics
- WebRTC video tracks (handled by WebRTC connection)

### Audio Topics
- `rt/audio_msg` - Speech recognition results
- `rt/vui/status` - Voice UI status

## 📝 Quick Commands

### Monitor All Topics
```bash
python3 listen_all_topics.py
```

### View LiDAR Live
```bash
python3 test_lidar_realtime.py
```

### Check Battery
```bash
python3 monitor_battery.py
```

## 🔍 Point Cloud Format

LiDAR data uses PointCloud2 format:
- **Fields**: x, y, z, intensity, tag, line
- **Encoding**: Little-endian float32 (x,y,z,intensity), uint8 (tag, line)
- **Rate**: 10-20 Hz typical
- **Points**: ~96,000 points/frame (Livox Mid-360)

## 🧪 Testing Workflow

1. **Verify topics exist**:
   ```bash
   python3 list_topics.py
   ```

2. **Test specific sensor**:
   ```bash
   python3 test_lidar_topics.py
   ```

3. **Monitor during operation**:
   ```bash
   python3 listen_telemetry.py
   ```

## 🚨 Important Notes

- **Topic prefix**: WebRTC uses `rt/lf/` for low-frequency variants
- **Message format**: Most topics use JSON-encoded DDS messages
- **Subscription**: Use `robot.subscribe(topic, callback)` from helpers
- **Performance**: Heavy point clouds may affect UI responsiveness
