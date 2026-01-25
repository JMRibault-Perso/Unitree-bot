# G1 Application - Project Status

## ✅ Completed

### Core Architecture (100%)
- [x] Event bus system (pub-sub for decoupled communication)
- [x] State machine with FSM transition validation
- [x] Command executor with all API payload builders
- [x] Robot controller orchestrator
- [x] API constants (all IDs, states, topics, enums)

### Sensor Managers (100%)
- [x] Odometry manager (500Hz/20Hz position/velocity)
- [x] LiDAR manager (10Hz point cloud, Mid-360 specs)
- [x] VUI manager (ASR, TTS, LED, audio)
- [x] Video manager (WebRTC video stream processing)

### Utilities (100%)
- [x] Configuration management (env vars + programmatic)
- [x] Logging setup (debug/info levels, file output)
- [x] Package initialization (__init__.py files)

### Testing & Documentation (100%)
- [x] CLI test interface (keyboard control)
- [x] Architecture documentation (README.md)
- [x] Development guide (usage examples)
- [x] Installation guide (setup instructions)

## 📋 TODO

### Phase 1: Core Testing & Refinement (NEXT)
1. **Test CLI Interface**
   - Run on actual robot
   - Verify all FSM transitions
   - Test motion control
   - Test gestures
   - Fix any bugs

2. **Test Sensor Managers**
   - Verify odometry data reception
   - Test LiDAR point cloud parsing
   - Test VUI (ASR/TTS/LED)
   - Verify video stream extraction
   - Fix data parsing issues

3. **Integration Testing**
   - Test event bus with multiple subscribers
   - Verify state machine transitions match robot behavior
   - Test sensor data flowing through events
   - Performance testing (handle 500Hz odometry)

### Phase 2: UI Implementation
Choose one or implement both:

#### Option A: Web UI (Recommended)
- [ ] FastAPI backend server
  - WebSocket endpoint for real-time events
  - REST API for commands
  - Static file serving
- [ ] React frontend
  - FSM state diagram display
  - Motion control joystick/buttons
  - Gesture buttons
  - Sensor data visualization (charts, 3D point cloud)
  - Video stream display
  - Voice command interface

#### Option B: Desktop UI
- [ ] PyQt6 application
  - Main window with tabs
  - Control panel
  - Sensor displays
  - Video feed
  - State diagram

### Phase 3: Advanced Features
- [ ] SLAM (mapping using LiDAR + odometry)
- [ ] Autonomous navigation
- [ ] Computer vision (object detection on video)
- [ ] Voice command processing (ASR → actions)
- [ ] Trajectory recording and playback
- [ ] Multi-robot coordination

### Phase 4: Production Ready
- [ ] Error recovery and resilience
- [ ] Logging and diagnostics
- [ ] Configuration file support
- [ ] Unit tests
- [ ] Integration tests
- [ ] Deployment packaging
- [ ] User documentation

## File Structure

```
/root/G1/unitree_sdk2/g1_app/
├── __init__.py                    ✅ Main package init
├── README.md                      ✅ Architecture overview
├── DEVELOPMENT_GUIDE.md           ✅ Usage guide
├── INSTALLATION.md                ✅ Setup instructions
├── PROJECT_STATUS.md              ✅ This file
│
├── core/                          ✅ Core functionality
│   ├── __init__.py
│   ├── event_bus.py              ✅ Pub-sub system
│   ├── state_machine.py          ✅ FSM tracking
│   ├── command_executor.py       ✅ Payload builders
│   └── robot_controller.py       ✅ Main orchestrator (needs sensor integration)
│
├── api/                           ✅ API definitions
│   ├── __init__.py
│   └── constants.py              ✅ All API IDs, states, topics
│
├── sensors/                       ✅ Sensor managers
│   ├── __init__.py
│   ├── odometry_manager.py       ✅ Position/velocity
│   ├── lidar_manager.py          ✅ Point cloud
│   ├── vui_manager.py            ✅ Voice/LED/audio
│   └── video_manager.py          ✅ Video streaming
│
├── utils/                         ✅ Utilities
│   ├── __init__.py
│   ├── config.py                 ✅ Configuration
│   └── logger.py                 ✅ Logging setup
│
├── cli_test.py                    ✅ CLI interface
│
├── ui/                            ⏳ UI implementations (TODO)
│   ├── web/                      ⏳ Web UI
│   │   ├── backend/              ⏳ FastAPI server
│   │   └── frontend/             ⏳ React app
│   └── desktop/                  ⏳ PyQt6 app
│
└── tests/                         ⏳ Test suite (TODO)
    ├── test_core.py
    ├── test_sensors.py
    └── test_integration.py
```

## Architecture Highlights

### Event-Driven Design
- **EventBus**: Decouples sensors from UI
- **Events**: STATE_CHANGED, ODOMETRY, LIDAR_CLOUD, VIDEO_FRAME, ASR_TEXT, ERROR
- **Benefits**: Multiple subscribers, easy to add new features, testable

### State Machine Safety
- **TRANSITIONS dict**: Enforces valid FSM state changes
- **can_transition()**: Validates before sending command
- **Emergency transitions**: Always allow DAMP/ZERO_TORQUE
- **Benefits**: Prevents invalid commands, matches official state diagram

### Modular Sensor Processing
- **OdometryManager**: Subscribes to rt/odommodestate, parses, emits events
- **LiDARManager**: Processes PointCloud2, applies mount transform
- **VUIManager**: Handles ASR/TTS/LED with high-level API
- **VideoManager**: Extracts frames from WebRTC, decodes H.264
- **Benefits**: Independent testing, easy to disable, clean separation

### Command Abstraction
- **CommandExecutor**: Builds JSON payloads for all APIs
- **High-level methods**: walk_forward(), wave_hand(), etc.
- **Safety**: Velocity clamping, continuous mode duration
- **Benefits**: Clean API, payload details hidden, easy to extend

## Integration Points

### With go2_webrtc_connect Library
```python
# robot_controller.py uses:
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

# Creates connection:
self.conn = UnitreeWebRTCConnection(
    WebRTCConnectionMethod.LocalSTA,
    ip=self.robot_ip,
    serialNumber=self.robot_sn
)
```

### Data Flow
```
Robot (G1 Air)
    ↓ WebRTC (WiFi)
UnitreeWebRTCConnection
    ↓ datachannel
CommandExecutor ──→ rt/api/sport/request (commands)
                ──→ rt/api/arm/request
    ↑ datachannel
SensorManagers ←── rt/sportmodestate (state)
               ←── rt/odommodestate (odometry)
               ←── rt/utlidar/* (LiDAR)
               ←── rt/audio_msg (ASR)
    ↓ EventBus
UI (Web/Desktop) ←── Events (ODOMETRY, LIDAR_CLOUD, etc.)
```

## Testing Strategy

### Unit Testing
- Test each component in isolation
- Mock datachannel for command tests
- Mock EventBus for sensor tests
- Verify state machine transitions

### Integration Testing
- Test full command flow: UI → Controller → Executor → Robot
- Test sensor flow: Robot → Managers → EventBus → UI
- Test state synchronization
- Test error handling

### System Testing
- Run on actual robot
- Test all FSM states
- Test all motion commands
- Test all gestures
- Verify sensor data accuracy
- Performance testing (handle high-frequency data)

## Performance Considerations

### High-Frequency Data
- Odometry: 500Hz (need efficient parsing)
- LiDAR IMU: 200Hz
- Video: 30 FPS

### Solutions
- Event bus is thread-safe with Lock
- Sensor managers run in separate threads
- UI updates throttled (don't render every frame)
- Data buffering for sensor fusion

## Security Considerations

- No authentication in WebRTC connection (robot-side limitation)
- Network traffic not encrypted (WebRTC limitation)
- Assume trusted network environment
- Future: Add auth layer in UI (if deploying web interface)

## Next Immediate Steps

1. **Test on Robot**
   ```bash
   python3 -m g1_app.cli_test
   # Try: d, r, w, s, g commands
   ```

2. **Debug Sensor Data**
   - Add print statements in sensor managers
   - Verify data format from robot
   - Fix parsing if needed

3. **Choose UI Framework**
   - Web UI: Better for remote control, multiple devices
   - Desktop UI: Better for local control, lower latency

4. **Implement UI**
   - Start with simple control buttons
   - Add sensor visualization
   - Add video stream display

## Resources

### Documentation
- [G1_AIR_CONTROL_GUIDE.md](../G1_AIR_CONTROL_GUIDE.md) - Complete API reference
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Command quick reference
- [README.md](README.md) - Architecture overview
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Usage examples
- [INSTALLATION.md](INSTALLATION.md) - Setup guide

### Official Unitree Docs
- [LiDAR Service](https://support.unitree.com/home/en/G1_developer/lidar)
- [VUI Service](https://support.unitree.com/home/en/G1_developer/Audio)
- [Odometry Service](https://support.unitree.com/home/en/G1_developer/Odometry)

### Libraries
- go2_webrtc_connect: `/root/G1/go2_webrtc_connect`
- Python asyncio: Standard library
- Future: FastAPI, React, PyQt6, OpenCV, numpy

## Known Limitations

### G1 Air Constraints
- **No DDS**: WebRTC only (can't use SDK examples directly)
- **No SSH**: Can't access robot OS
- **WiFi only**: Must be on same network
- **Pre-configured**: Can't change robot-side settings

### Application Constraints
- **Single connection**: One client at a time
- **Network dependent**: Latency affects control
- **No offline mode**: Requires active connection
- **Data parsing**: May need adjustment based on actual robot messages

## Future Enhancements

- Multi-robot control (fleet management)
- Cloud integration (telemetry, remote access)
- AI integration (autonomous behaviors)
- AR visualization (robot state overlay)
- Mobile app (Android/iOS version)
- ROS2 bridge (integrate with ROS ecosystem)
