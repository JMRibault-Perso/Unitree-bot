# G1 Application - Quick Reference

## Installation
```bash
cd /root/G1/unitree_sdk2
pip3 install asyncio numpy
export G1_ROBOT_IP=192.168.86.16
export G1_ROBOT_SN=E21D1000PAHBMB06
```

## Quick Start
```bash
# Run CLI interface
python3 -m g1_app.cli_test

# Commands:
# d - Damp      r - Ready     s - Sit
# w - Forward   x - Backward  SPACE - Stop
# g - Wave      i - Info      h - Help
```

## Basic Usage
```python
import asyncio
from g1_app import RobotController, EventBus, Events

async def main():
    # Create and connect
    robot = RobotController("192.168.86.16", "E21D1000PAHBMB06")
    await robot.connect()
    
    # Control
    await robot.damp()       # Emergency stop
    await robot.ready()      # Stand ready
    await robot.forward(0.3) # Walk forward
    await robot.stop()       # Stop
    
    await robot.disconnect()

asyncio.run(main())
```

## FSM States
```
ZERO_TORQUE (0)  - Motors off
DAMP (1)         - Safe mode (orange LED)
START (200)      - Ready (blue LED)
SIT (3)          - Sitting (green LED)
```

## Motion Control
```python
# Velocity control (requires START state)
await robot.set_velocity(vx=0.5, vy=0.0, omega=0.0)

# High-level methods
await robot.forward(0.3)    # vx: 0 to 0.8 m/s
await robot.backward(0.3)   # vx: -0.8 to 0
await robot.left(0.2)       # vy: -0.5 to 0.5 m/s
await robot.right(0.2)
await robot.turn_left(0.5)  # omega: -1.0 to 1.0 rad/s
await robot.turn_right(0.5)
await robot.stop()
```

## Gestures
```python
# Execute gesture
await robot.execute_gesture("wave_hand")

# Common gestures:
# - wave_hand, shake_left_hand, shake_right_hand
# - heart, namaste, stretch

# Custom actions (teach mode)
await robot.executor.execute_custom_action("my_dance")
await robot.executor.stop_custom_action()
```

## Event System
```python
from g1_app import EventBus, Events

# Subscribe to events
def on_state_change(state):
    print(f"State: {state.fsm_state.name}")

EventBus.subscribe(Events.STATE_CHANGED, on_state_change)

# Available events:
# - STATE_CHANGED, CONNECTION_CHANGED
# - ODOMETRY, LIDAR_CLOUD, VIDEO_FRAME, ASR_TEXT
```

## Sensors

### Odometry (500Hz)
```python
def on_odom(odom):
    print(f"Pos: ({odom.x}, {odom.y}), Vel: {odom.vx}")

EventBus.subscribe(Events.ODOMETRY, on_odom)
current = robot.odom_manager.get_current()
```

### LiDAR (10Hz)
```python
def on_lidar(cloud):
    print(f"{cloud.point_count} points")
    for pt in cloud.points[:10]:
        print(f"({pt.x}, {pt.y}, {pt.z})")

EventBus.subscribe(Events.LIDAR_CLOUD, on_lidar)
```

### Voice (VUI)
```python
from g1_app.api import LEDColor, TTSSpeaker

# Speech recognition
def on_speech(asr):
    print(f"Heard: {asr.text}")

EventBus.subscribe(Events.ASR_TEXT, on_speech)

# Text-to-speech
robot.vui_manager.speak("Hello", TTSSpeaker.FEMALE)

# LED control
robot.vui_manager.set_led_color(LEDColor.BLUE)
robot.vui_manager.set_led_brightness(200)
```

### Video
```python
def on_frame(frame):
    print(f"{frame.width}x{frame.height}")

EventBus.subscribe(Events.VIDEO_FRAME, on_frame)
snapshot = robot.video_manager.take_snapshot()
```

## Configuration
```python
from g1_app.utils import Config, RobotConfig

config = Config(
    robot=RobotConfig(ip="192.168.86.16", serial_number="..."),
)
```

Or use environment variables:
```bash
export G1_ROBOT_IP=192.168.86.16
export G1_ROBOT_SN=E21D1000PAHBMB06
export G1_ENABLE_LIDAR=true
```

## Error Handling
```python
try:
    await robot.connect()
    await robot.ready()
except Exception as e:
    print(f"Error: {e}")
    await robot.emergency_stop()
finally:
    await robot.disconnect()
```

## Debugging
```python
from g1_app.utils import setup_app_logging

# Enable debug logs
setup_app_logging(verbose=True)

# Check state
print(robot.current_state.fsm_state.name)
print(robot.is_connected)

# Valid transitions
allowed = robot.state_machine.get_allowed_transitions()
print([s.name for s in allowed])
```

## API Constants
```python
from g1_app.api import LocoAPI, ArmAPI, FSMState, LEDColor

# API IDs
LocoAPI.SET_FSM_ID      # 7101
LocoAPI.SET_VELOCITY    # 7105
ArmAPI.EXECUTE_ACTION   # 7106

# States
FSMState.DAMP           # 1
FSMState.START          # 200
FSMState.SIT            # 3

# Colors
LEDColor.ORANGE         # Damp mode
LEDColor.BLUE           # Normal
LEDColor.RED            # Error
```

## File Locations
```
/root/G1/unitree_sdk2/g1_app/
├── README.md               - Architecture
├── INSTALLATION.md         - Setup guide
├── DEVELOPMENT_GUIDE.md    - Detailed usage
├── PROJECT_STATUS.md       - Implementation status
├── QUICK_REFERENCE.md      - This file
└── cli_test.py             - Test interface
```

## Common Issues

**Connection fails:**
- Check robot is on and WiFi connected
- Verify IP with `ping 192.168.86.16`
- Test with Android app first

**State transition rejected:**
```python
# Check allowed transitions
allowed = robot.state_machine.get_allowed_transitions()
# Always allowed: DAMP, ZERO_TORQUE
```

**No sensor data:**
```python
# Verify managers exist
print(robot.odom_manager is not None)
# Enable debug logging
setup_app_logging(verbose=True)
```

## Resources

- [Full Development Guide](DEVELOPMENT_GUIDE.md)
- [Installation Instructions](INSTALLATION.md)
- [G1 Air Control Guide](../G1_AIR_CONTROL_GUIDE.md)
- [Unitree Official Docs](https://support.unitree.com/home/en/G1_developer)
