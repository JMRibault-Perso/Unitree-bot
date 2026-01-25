# G1 Application - Development Guide

## Overview

This document provides a comprehensive guide to using and extending the G1 robot control application.

## Architecture Summary

```
g1_app/
├── core/               # Core functionality
│   ├── event_bus.py   # Pub-sub event system
│   ├── state_machine.py  # FSM tracking
│   ├── command_executor.py  # Command builders
│   └── robot_controller.py  # Main orchestrator
├── api/               # API definitions
│   └── constants.py   # All API IDs, states, topics
├── sensors/           # Sensor managers
│   ├── odometry_manager.py  # Position/velocity
│   ├── lidar_manager.py     # Point cloud
│   ├── vui_manager.py       # Voice/LED/audio
│   └── video_manager.py     # Video streaming
├── utils/             # Utilities
│   ├── config.py      # Configuration
│   └── logger.py      # Logging setup
└── cli_test.py        # CLI testing interface
```

## Quick Start

### 1. Installation

```bash
cd /root/G1/unitree_sdk2

# Install dependencies
pip3 install asyncio

# Configure robot (edit if needed)
export G1_ROBOT_IP=192.168.86.16
export G1_ROBOT_SN=E21D1000PAHBMB06
```

### 2. Run CLI Test Interface

```bash
python3 -m g1_app.cli_test
```

Available commands:
- `d` - Damp mode (emergency stop)
- `r` - Ready mode (stand up)
- `w` - Walk forward
- `s` - Sit down
- `g` - Wave hand gesture
- `i` - Show current state
- `h` - Help

### 3. Basic Usage Example

```python
import asyncio
from g1_app import RobotController, EventBus, Events, FSMState

async def main():
    # Create controller
    controller = RobotController("192.168.86.16", "E21D1000PAHBMB06")
    
    # Subscribe to state changes
    def on_state_change(state):
        print(f"State: {state.fsm_state.name}, LED: {state.led_color.value}")
    
    EventBus.subscribe(Events.STATE_CHANGED, on_state_change)
    
    # Connect and control
    await controller.connect()
    
    await controller.damp()       # Emergency stop
    await asyncio.sleep(2)
    
    await controller.ready()      # Stand ready
    await asyncio.sleep(3)
    
    await controller.forward(0.3) # Walk forward at 0.3 m/s
    await asyncio.sleep(5)
    
    await controller.stop()       # Stop motion
    await controller.damp()       # Safe shutdown
    
    await controller.disconnect()

asyncio.run(main())
```

## Sensor Integration

### Odometry

```python
from g1_app.sensors import OdometryManager

# Subscribe to odometry updates
def on_odometry(odom_data):
    print(f"Position: ({odom_data.x:.2f}, {odom_data.y:.2f}, {odom_data.z:.2f})")
    print(f"Velocity: ({odom_data.vx:.2f}, {odom_data.vy:.2f})")

EventBus.subscribe(Events.ODOMETRY, on_odometry)

# Odometry is automatically started by RobotController
# Access current data:
current_odom = controller.odom_manager.get_current()
```

### LiDAR

```python
from g1_app.sensors import LiDARManager

def on_lidar_cloud(cloud_data):
    print(f"Point cloud: {cloud_data.point_count} points")
    
    # Process points
    for point in cloud_data.points[:10]:  # First 10 points
        print(f"  ({point.x:.2f}, {point.y:.2f}, {point.z:.2f})")

EventBus.subscribe(Events.LIDAR_CLOUD, on_lidar_cloud)

# Apply robot-frame transform
if controller.lidar_manager:
    cloud = controller.lidar_manager.get_current_cloud()
    if cloud:
        transformed = controller.lidar_manager.apply_mount_transform(cloud.points)
```

### Voice User Interface (VUI)

```python
from g1_app.sensors import VUIManager
from g1_app.api import LEDColor, TTSSpeaker

# Speech recognition
def on_asr(asr_result):
    print(f"Heard: '{asr_result.text}' (confidence: {asr_result.confidence})")

EventBus.subscribe(Events.ASR_TEXT, on_asr)

# Text-to-speech
controller.vui_manager.speak("Hello, I am G1", TTSSpeaker.FEMALE)

# LED control
controller.vui_manager.set_led_color(LEDColor.BLUE)
controller.vui_manager.set_led_brightness(200)

# Play audio
controller.vui_manager.play_audio(1)
```

### Video

```python
from g1_app.sensors import VideoManager

async def on_video_frame(frame):
    print(f"Frame: {frame.width}x{frame.height}, {frame.format}")
    # Process frame data (H.264 encoded)

EventBus.subscribe(Events.VIDEO_FRAME, on_video_frame)

# Take snapshot
if controller.video_manager:
    snapshot = controller.video_manager.take_snapshot()
```

## FSM State Management

### Valid State Transitions

The state machine enforces valid transitions based on the official G1 state diagram:

```python
# Check if transition is valid
can_stand = controller.state_machine.can_transition(FSMState.SQUAT_TO_STAND)

# Get allowed transitions from current state
allowed = controller.state_machine.get_allowed_transitions()
print(f"Can transition to: {[s.name for s in allowed]}")

# Emergency transitions (always allowed)
await controller.emergency_stop()  # Goes to DAMP immediately
```

### State Diagram

```
ZERO_TORQUE (0) ──┬──> DAMP (1) ──> START (200) ──┬──> SQUAT_TO_STAND (706) ──> START
                  │                                │
                  └─────────────> SIT (3) ─────────┘
                                    │
                                    └──> STAND_TO_SQUAT (707) ──> SIT
```

## Gesture Control

### Pre-programmed Gestures

```python
from g1_app.api import ArmGesture

# Execute specific gesture
await controller.execute_gesture("wave_hand")

# Or use gesture ID
await controller.executor.execute_gesture(ArmGesture.WAVE)

# Available gestures:
# - RELEASE_ARM (99): Release arm control
# - WAVE (25): Wave hand
# - HEART (20): Heart gesture
# - SHAKE_LEFT (11): Left handshake
# - SHAKE_RIGHT (12): Right handshake
# And more...

# Get full gesture list from robot
gestures = await controller.executor.get_gesture_list()
for g in gestures:
    print(f"{g['id']}: {g['name']}")
```

### Teach Mode (Custom Actions)

```python
# Execute recorded custom action
await controller.executor.execute_custom_action("my_dance")

# Stop custom action
await controller.executor.stop_custom_action()
```

## Motion Control

### Velocity Control

```python
# Forward/backward (vx: -0.8 to 0.8 m/s)
await controller.set_velocity(vx=0.5, vy=0, omega=0)

# Strafe left/right (vy: -0.5 to 0.5 m/s)
await controller.set_velocity(vx=0, vy=0.3, omega=0)

# Turn (omega: -1.0 to 1.0 rad/s)
await controller.set_velocity(vx=0, vy=0, omega=0.5)

# Combined motion
await controller.set_velocity(vx=0.3, vy=0.1, omega=0.2)

# Stop
await controller.stop()
```

### High-level Convenience Methods

```python
await controller.forward(speed=0.3)   # Walk forward
await controller.backward(speed=0.3)  # Walk backward
await controller.left(speed=0.2)      # Strafe left
await controller.right(speed=0.2)     # Strafe right
await controller.turn_left(omega=0.5) # Turn left
await controller.turn_right(omega=0.5)# Turn right
await controller.stop()               # Stop all motion
```

## Event System

### Available Events

```python
from g1_app import Events

# Robot state
Events.STATE_CHANGED    # FSM state changes
Events.CONNECTION_CHANGED # Connection status

# Sensors
Events.ODOMETRY         # Position/velocity updates (500Hz or 20Hz)
Events.LIDAR_CLOUD      # Point cloud data (10Hz)
Events.LIDAR_IMU        # LiDAR IMU data (200Hz)
Events.VIDEO_FRAME      # Video frames (30Hz)
Events.ASR_TEXT         # Speech recognition results

# System
Events.ERROR            # Error events
Events.COMMAND_SENT     # Command sent
Events.COMMAND_RESPONSE # Command response
```

### Event Subscription

```python
# Subscribe to event
def my_handler(data):
    print(f"Received: {data}")

EventBus.subscribe(Events.ODOMETRY, my_handler)

# Unsubscribe
EventBus.unsubscribe(Events.ODOMETRY, my_handler)

# Clear all handlers for an event
EventBus.clear(Events.ODOMETRY)
```

## Configuration

### Environment Variables

```bash
# Robot connection
export G1_ROBOT_IP=192.168.86.16
export G1_ROBOT_SN=E21D1000PAHBMB06
export G1_TIMEOUT=10.0

# Sensor enable/disable
export G1_ENABLE_ODOM=true
export G1_ENABLE_LIDAR=true
export G1_ENABLE_VUI=true
export G1_ENABLE_VIDEO=true

# UI configuration
export G1_UI_TYPE=web        # 'web' or 'desktop'
export G1_UI_HOST=0.0.0.0
export G1_UI_PORT=8000
export G1_UI_WS_PORT=8001
```

### Programmatic Configuration

```python
from g1_app.utils import Config, RobotConfig, SensorConfig

config = Config(
    robot=RobotConfig(
        ip="192.168.86.16",
        serial_number="E21D1000PAHBMB06",
        timeout=10.0
    ),
    sensors=SensorConfig(
        enable_lidar=True,
        lidar_transform=True,
        video_fps=30
    )
)

# Use in controller
controller = RobotController(
    config.robot.ip,
    config.robot.serial_number
)
```

## Logging

### Enable Debug Logging

```python
from g1_app.utils import setup_app_logging

# Enable debug mode
setup_app_logging(verbose=True)

# Or configure specific logger
import logging
logging.getLogger('g1_app.core').setLevel(logging.DEBUG)
```

## Error Handling

```python
from g1_app import RobotController, FSMState

async def safe_control():
    controller = RobotController("192.168.86.16", "E21D1000PAHBMB06")
    
    try:
        await controller.connect()
        
        # Attempt state transition
        success = await controller.set_fsm_state(FSMState.START)
        if not success:
            print("Transition failed - invalid from current state")
        
        # Motion control with validation
        if controller.state_machine.is_ready_for_motion():
            await controller.forward(0.3)
        else:
            print("Robot not ready for motion")
        
    except Exception as e:
        print(f"Error: {e}")
        await controller.emergency_stop()
    
    finally:
        await controller.disconnect()
```

## Next Steps

### Adding UI (Web Interface)

See the main [README.md](README.md) for UI implementation options:
- **Web UI**: FastAPI backend + React frontend
- **Desktop UI**: PyQt6 native application

### Extending Functionality

1. **Custom Sensor Processing**: Subclass sensor managers
2. **Advanced Motion**: Implement trajectory planning
3. **Computer Vision**: Process video frames with OpenCV
4. **Mapping**: Build SLAM using LiDAR + odometry
5. **Voice Commands**: Add speech-to-action pipeline

## Troubleshooting

### Robot Not Responding

```python
# Check connection
print(controller.is_connected)

# Check current state
print(controller.current_state.fsm_state.name)

# Emergency stop
await controller.emergency_stop()
```

### No Sensor Data

```python
# Verify sensor managers are running
print(controller.odom_manager is not None)
print(controller.lidar_manager is not None)

# Subscribe to events with debug handler
def debug_handler(data):
    print(f"Event received: {data}")

EventBus.subscribe(Events.ODOMETRY, debug_handler)
```

### State Transition Rejected

```python
# Check allowed transitions
current = controller.current_state.fsm_state
allowed = controller.state_machine.get_allowed_transitions()
print(f"Current: {current.name}")
print(f"Can transition to: {[s.name for s in allowed]}")

# Use emergency transitions
await controller.damp()  # Always allowed
```

## API Reference

For complete API documentation, see:
- [G1_AIR_CONTROL_GUIDE.md](../G1_AIR_CONTROL_GUIDE.md) - Discovery process and API details
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Command quick reference
- [README.md](README.md) - Architecture overview

Official Unitree documentation:
- [LiDAR Service](https://support.unitree.com/home/en/G1_developer/lidar)
- [VUI Service](https://support.unitree.com/home/en/G1_developer/Audio)
- [Odometry Service](https://support.unitree.com/home/en/G1_developer/Odometry)
