# G1 Robot Control Application

Complete Android app replacement for Unitree G1 Air robot control via WebRTC.

## Architecture Overview

```
g1_app/
├── core/                  # Core robot control
│   ├── robot_controller.py    # Main controller (WebRTC connection, state management)
│   ├── state_machine.py       # FSM state tracking and transitions
│   ├── command_executor.py    # Command execution and payload building
│   └── event_bus.py           # Pub-sub event system
│
├── api/                   # API definitions and builders
│   ├── loco_api.py           # Locomotion APIs (FSM, velocity, gestures)
│   ├── arm_api.py            # Arm action APIs (gestures, teach mode)
│   ├── vui_api.py            # Voice/audio/LED APIs
│   └── constants.py          # All API IDs and enums
│
├── sensors/               # Sensor data managers
│   ├── lidar_manager.py      # LiDAR point cloud processing
│   ├── odometry_manager.py   # Position/velocity tracking
│   ├── vui_manager.py        # ASR/TTS/audio handling
│   └── video_manager.py      # Camera stream handling
│
├── ui/                    # User interface (future)
│   ├── web/                  # Web-based UI (Flask/FastAPI)
│   └── desktop/              # Desktop UI (PyQt/Tkinter)
│
└── utils/                 # Utilities
    ├── config.py             # Configuration management
    └── logger.py             # Logging setup
```

## Design Principles

1. **Separation of Concerns**: Core logic separate from UI
2. **Event-Driven**: Pub-sub pattern for sensor data distribution
3. **State Machine**: Explicit FSM tracking with transition validation
4. **Modularity**: Each subsystem (lidar, odometry, etc.) is independent
5. **Extensibility**: Easy to add new commands/sensors/UI backends

## Key Components

### RobotController
- Manages WebRTC connection to robot
- Coordinates command execution
- Routes sensor data to appropriate managers
- Emits state change events

### StateMachine
- Tracks current FSM state (Damp, Ready, Walking, etc.)
- Validates state transitions per official diagram
- Maps states to LED colors
- Prevents invalid commands

### CommandExecutor
- Builds correct API payloads
- Handles different services (sport, arm)
- Provides high-level command methods
- Manages command queuing

### SensorManagers
- Subscribe to DDS topics via WebRTC
- Parse and process sensor data
- Emit processed data via EventBus
- Independent operation

### EventBus
- Central pub-sub system
- Allows UI to subscribe to any data stream
- Decouples sensors from UI
- Thread-safe event delivery

## Communication Flow

```
UI Request → RobotController → StateMachine (validate)
                             → CommandExecutor (build payload)
                             → WebRTC Connection → Robot

Robot → WebRTC → RobotController → SensorManager (parse)
                                 → EventBus (emit)
                                 → UI (subscribe)
```

## State Machine (FSM)

Based on official diagram:
```
PowerOn → ZeroTorque(0) → Damp(1) → Ready(200) → Walking/Running
                                  → Sit(3)
                                  → Squat2Stand(706)
                                  → Stand2Squat(707)
                                  → LyingStand(708)
```

LED Color Mapping:
- Orange: Damp Mode
- Blue: Normal Operation  
- Purple: Zero Torque
- Green: Seated
- Yellow: Debug Mode
- Dark Blue: Standby
- Red: Error State

## API Services

### Sport Service (locomotion)
- 7101: SetFsmId - Change FSM state
- 7105: SetVelocity - Movement control
- 7106: SetTaskId - Arm gestures (wave, shake hand)

### Arm Service (actions)
- 7106: ExecuteAction - Pre-programmed gestures
- 7107: GetActionList - Retrieve all custom actions stored on robot
- 7108: ExecuteCustomAction - Play a custom action by name
- 7109: StartRecordAction - Begin recording arm movements
- 7110: StopRecordAction - Stop recording without saving
- 7111: SaveRecordedAction - Save recording with name and duration
- 7112: DeleteAction - Delete a custom action from robot
- 7113: StopCustomAction - Emergency stop during playback
- 7114: RenameAction - Rename an existing custom action
- 7113: StopCustomAction - Stop teach playback

### Audio Service (VUI)
- TTS, volume, LED, ASR via topic subscriptions

## Sensor Topics

- `rt/sportmodestate` - FSM state, task ID
- `rt/odommodestate` - Position, velocity (500Hz)
- `rt/lf/odommodestate` - Position, velocity (20Hz)
- `rt/utlidar/cloud_livox_mid360` - LiDAR point cloud (10Hz)
- `rt/utlidar/imu_livox_mid360` - LiDAR IMU (200Hz)
- `rt/audio_msg` - ASR text results
- WebRTC video track - Camera stream

## Usage

```python
from core.robot_controller import RobotController
from core.event_bus import EventBus

# Initialize
controller = RobotController("192.168.86.16", "E21D1000PAHBMB06")
await controller.connect()

# Subscribe to events
def on_state_change(state):
    print(f"Robot state: {state.name}, LED: {state.led_color}")

EventBus.subscribe("state_changed", on_state_change)

# Send commands
await controller.set_fsm_state("damp")
await controller.set_velocity(vx=0.3, vy=0, omega=0)  # Walk forward
await controller.execute_gesture("wave_hand")

# Sensor data automatically flows to subscribers
def on_odometry(data):
    print(f"Position: {data.position}, Velocity: {data.velocity}")

EventBus.subscribe("odometry", on_odometry)
```

## Future UI Options

### Option 1: Web UI (Recommended)
- **Backend**: FastAPI with WebSocket for real-time updates
- **Frontend**: React/Vue with Canvas for LiDAR/video
- **Pros**: Cross-platform, modern, easy deployment
- **Cons**: Requires web server

### Option 2: Desktop UI
- **Framework**: PyQt6 or Tkinter
- **Pros**: Native feel, no web dependency
- **Cons**: Platform-specific builds

### Option 3: Hybrid
- Web UI for remote control
- Desktop UI for local development/testing

## Development Phases

**Phase 1**: Core architecture (robot_controller, state_machine, event_bus)
**Phase 2**: Command execution (all APIs implemented)
**Phase 3**: Sensor managers (lidar, odometry, vui)
**Phase 4**: CLI interface for testing
**Phase 5**: Web UI development
**Phase 6**: Polish and deployment

## Configuration

`config.yaml`:
```yaml
robot:
  ip: "192.168.86.16"
  serial: "E21D1000PAHBMB06"
  
sensors:
  lidar_enabled: true
  odometry_hz: 20  # Use low-freq topic
  video_enabled: true
  
control:
  max_velocity: 0.5  # m/s
  velocity_ramp: 0.1  # m/s² acceleration
  
ui:
  type: "web"  # or "desktop"
  port: 8000
```

## Next Steps

1. Implement core modules (controller, state machine, event bus)
2. Add all API definitions and payload builders
3. Implement sensor managers
4. Create CLI for testing
5. Design web UI mockup
6. Implement UI backend (FastAPI + WebSocket)
7. Build React frontend
