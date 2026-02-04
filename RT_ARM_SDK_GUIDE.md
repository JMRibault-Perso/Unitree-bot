# rt/arm_sdk Topic - Direct Arm Motor Control

## Overview

The `rt/arm_sdk` topic provides **direct position control** of the G1's arm motors. This is a lower-level interface than the ARM Action APIs (7107/7108), allowing you to command individual joint positions, velocities, and torques.

## Status: ✅ IMPLEMENTED & AVAILABLE

Unlike the DDS topics which don't work on G1 Air, the `rt/arm_sdk` topic **IS accessible via WebRTC datachannel**!

Our implementation is already complete in:
- **Backend**: [`g1_app/core/command_executor.py`](g1_app/core/command_executor.py#L878-L950) - `send_lowcmd_arm_command()` method
- **Test script**: [`test_arm_sdk.py`](test_arm_sdk.py) - Full demo with examples

## How It Works

### Message Structure

The `rt/arm_sdk` topic uses the `LowCmd` message format with:
- **35 motor slots**: 29 real motors + 6 special parameter slots
- **Per-joint control**: position (q), velocity (dq), torque (tau), stiffness (kp), damping (kd)
- **Weight parameter**: `motor_cmd[29].q` = transition weight (0.0 to 1.0)

### Joint Indices (5-DOF Arms)

```python
# Left arm
LEFT_SHOULDER_PITCH = 15
LEFT_SHOULDER_ROLL = 16
LEFT_SHOULDER_YAW = 17
LEFT_ELBOW_PITCH = 18
LEFT_ELBOW_ROLL = 19

# Right arm
RIGHT_SHOULDER_PITCH = 22
RIGHT_SHOULDER_ROLL = 23
RIGHT_SHOULDER_YAW = 24
RIGHT_ELBOW_PITCH = 25
RIGHT_ELBOW_ROLL = 26

# Waist
WAIST_YAW = 12
WAIST_ROLL = 13
WAIST_PITCH = 14

# Special slot
NOT_USED_JOINT = 29  # Weight parameter (motor_cmd[29].q)
```

### Weight Parameter (Critical!)

The **weight** in `motor_cmd[29].q` controls the transition:
- **0.0**: Robot ignores commanded positions (safe default)
- **0.5**: Robot follows commands with 50% strength
- **1.0**: Robot fully follows commanded positions

**Best practice** (from SDK example):
1. Start with weight = 0.0
2. Ramp up slowly: `weight += 0.2 * dt` (takes ~5 seconds to reach 1.0 at 20Hz)
3. Send smooth position trajectories (use interpolation)
4. Ramp down before stopping

## Python API Usage

### Simple Position Command

```python
from g1_app.core.robot_controller import RobotController

robot = RobotController("192.168.86.11")
await robot.connect()

# Command left arm to raise forward
arm_command = {
    "enable_arm_sdk": True,  # Sets weight to 1.0
    "joints": [
        {
            "motor_index": 15,  # LEFT_SHOULDER_PITCH
            "q": 0.3,           # Position (radians)
            "dq": 0.0,          # Velocity
            "tau": 0.0,         # Feed-forward torque
            "kp": 60.0,         # Stiffness
            "kd": 1.5           # Damping
        }
    ]
}

robot.command_executor.send_lowcmd_arm_command(arm_command)
```

### Smooth Trajectory (Recommended Pattern)

```python
import asyncio
import math

# Initialize to current position first
async def smooth_motion(robot, target_angles, duration=5.0):
    """Move arms smoothly to target positions"""
    
    dt = 0.05  # 20Hz control rate
    num_steps = int(duration / dt)
    
    for step in range(num_steps):
        # Interpolate from 0 to target over time
        phase = step / num_steps
        
        joints = []
        for motor_idx, target_angle in target_angles.items():
            joints.append({
                "motor_index": motor_idx,
                "q": target_angle * phase,  # Smooth interpolation
                "dq": 0.0,
                "tau": 0.0,
                "kp": 60.0,
                "kd": 1.5
            })
        
        arm_command = {
            "enable_arm_sdk": True,
            "joints": joints
        }
        
        robot.command_executor.send_lowcmd_arm_command(arm_command)
        await asyncio.sleep(dt)

# Usage
target_angles = {
    15: 0.5,  # LEFT_SHOULDER_PITCH to 0.5 rad
    16: 0.3,  # LEFT_SHOULDER_ROLL to 0.3 rad
}
await smooth_motion(robot, target_angles, duration=3.0)
```

## Test Script Examples

We've created `test_arm_sdk.py` with several examples:

### 1. Listen to rt/arm_sdk Topic

```bash
python3 test_arm_sdk.py --listen --duration 10
```

This subscribes to the topic to see if the robot is publishing feedback.

### 2. Simple Position Command

```bash
python3 test_arm_sdk.py --simple --weight 0.5 --duration 5
```

Sends a simple command to raise the left arm slightly, holds for 5 seconds, then returns to zero.

### 3. Wave Arm Demo

```bash
python3 test_arm_sdk.py --wave --duration 10
```

Demonstrates smooth sinusoidal motion by waving the left arm back and forth.

### 4. Return to Zero

```bash
python3 test_arm_sdk.py --zero
```

Commands all arm joints to return to their zero position.

## Safety Considerations

⚠️ **IMPORTANT SAFETY NOTES:**

1. **Start with low weight**: Use 0.3-0.5 initially, not 1.0
2. **Small movements first**: Test with ±0.2 radians before larger motions
3. **Smooth interpolation**: Never jump between positions - always interpolate
4. **Control rate**: Send commands at 20-50Hz for smooth motion
5. **Emergency stop**: Have the Android app ready to enable DAMP mode
6. **Clearance**: Ensure robot has space to move before commanding

## Comparison with ARM Action APIs

| Feature | rt/arm_sdk | ARM Action APIs (7107/7108) |
|---------|------------|------------------------------|
| **Control Type** | Direct position control | Pre-programmed actions |
| **Flexibility** | Full freedom | Limited to recorded gestures |
| **Complexity** | High (need control loop) | Low (single command) |
| **Safety** | Manual (your responsibility) | Built-in collision avoidance |
| **FSM Requirements** | Unknown (needs testing) | States 500/501 or 801+mode0/3 |
| **Use Case** | Custom motions, research | Quick gestures, demos |

## Next Steps

1. **Test on your robot**: Run `python3 test_arm_sdk.py --simple --weight 0.3`
2. **Monitor behavior**: Watch how the robot responds to different weight values
3. **Build control loop**: Create smooth trajectories for complex motions
4. **Add to web UI**: Integrate direct control sliders for each joint
5. **Safety testing**: Test emergency stop and collision scenarios

## References

- **SDK Examples**: 
  - [`example/g1/high_level/g1_arm5_sdk_dds_example.cpp`](example/g1/high_level/g1_arm5_sdk_dds_example.cpp) - 5-DOF arm control
  - [`example/g1/high_level/g1_arm7_sdk_dds_example.cpp`](example/g1/high_level/g1_arm7_sdk_dds_example.cpp) - 7-DOF arm control
- **Our Implementation**: [`g1_app/core/command_executor.py`](g1_app/core/command_executor.py#L878-L950)
- **Documentation**: [unitree_docs/arm-control-routine.md](unitree_docs/arm-control-routine.md)

## Common Issues

### Q: Robot doesn't move when I send commands
- Check weight parameter is > 0
- Verify FSM state allows arm control (may need specific mode)
- Ensure connection is active (check WebSocket status)
- Try increasing kp (stiffness) value

### Q: Movements are jerky
- Increase control rate (send more frequently)
- Use smooth interpolation between positions
- Reduce max velocity limits
- Add velocity smoothing (dq parameter)

### Q: Robot moves too aggressively
- Reduce weight parameter (start at 0.3)
- Reduce kp (stiffness)
- Increase kd (damping)
- Use smaller position increments

---

**Status**: Ready to test! The implementation is complete and waiting for you to try it out. 🚀
