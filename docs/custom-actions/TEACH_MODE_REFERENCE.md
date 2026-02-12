# Teach Mode Implementation - Complete Reference

## Overview

This reference prioritizes **phone logs** and cross-checks the **Unitree Arm Action Service** documentation.

**Primary sources**:
- Phone logs (WebRTC datachannel JSON): action list/execute/rename/record via `rt/api/arm/request`
- Unitree Arm Action Service: https://support.unitree.com/home/en/G1_developer/arm_action_interface

## API Reference

### Phone-Log Confirmed (WebRTC JSON over `rt/api/arm/request`)

| API ID | Purpose | Parameters | Notes |
|--------|---------|------------|-------|
| 7107 | GetActionList | none | Returns preset + custom actions list |
| 7108 | ExecuteCustomAction | `action_name` (string) | Plays a taught action by name |
| 7109 | RenameAction | `pre_name`, `new_name` | Renames an existing custom action |
| 7110 | RecordCustomAction | `action_name` (string or empty) | Start/keep-alive/stop recording; empty stops |
| 7113 | StopCustomAction | none | Emergency stop for playback |

### Unitree Arm Action Service (SDK, EDU models)

From the official documentation:
- `ExecuteAction(int32_t action_id)` is **blocking** and plays preset actions.
- `ExecuteAction(const std::string &action_name)` is **non-blocking** and plays taught actions.
- `StopCustomAction()` stops playback and returns arms to the initial position.
- `GetActionList(std::string &data)` returns the available actions list.

### Preset Action IDs (Always Available)

From `sdk2_python/unitree_sdk2py/g1/arm/g1_arm_action_client.py`:

```python
action_map = {
    "release arm": 99,
    "two-hand kiss": 11,
    "left kiss": 12,
    "right kiss": 13,
    "hands up": 15,
    "clap": 17,
    "high five": 18,
    "hug": 19,
    "heart": 20,
    "right heart": 21,
    "reject": 22,
    "right hand up": 23,
    "x-ray": 24,
    "face wave": 25,
    "high wave": 26,
    "shake hand": 27,
}
```

## C++ SDK Implementation Reference

From `unitree_docs/arm-control-routine.md` and C++ examples:

### Arm Control Flow

**Key Concept**: Use weight parameter to smoothly transition motor control

```cpp
// Joint not used for control - use for weight transition
msg.motor_cmd().at(JointIndex::kNotUsedJoint).q(weight);  // weight: 0 → 1

// Weight controls smoothness:
// - 0 = motors free (disabled)
// - 0-1 = smooth transition
// - 1 = full control
```

### Motion Parameters

From `g1_arm5_sdk_dds_example.py` and C++ examples:

```python
# Control gains
kp = 50.0      # Stiffness (proportional)
kd = 5.0       # Damping (derivative)
tau_ff = 0.0   # Feedforward torque
dq = 0.0       # Velocity reference

# Timing
control_dt = 0.02       # 50 Hz control rate
duration = 5.0          # Typical motion duration

# Position limits
max_joint_delta = 0.1   # Max position change per cycle (smooth interpolation)
```

## Python SDK - Custom Action Notes

For EDU models that expose DDS, follow the **Arm Action Service** APIs from the Unitree documentation:
- `ExecuteAction(int32_t action_id)`
- `ExecuteAction(const std::string &action_name)`
- `StopCustomAction()`
- `GetActionList(std::string &data)`

Use the phone-log evidence above as the authoritative source for G1 Air behavior.

## Web Controller Integration

### Current Implementation (Web Server)

From `g1_app/core/robot_controller.py`:

```python
# Already has ExecuteCustomAction (API 7108)
async def execute_custom_action(self, action_name: str) -> dict:
    """Execute a custom taught action"""
    # Implementation present

# Already has StopCustomAction (API 7113)
async def stop_custom_action(self) -> dict:
    """Stop custom action"""
    # Implementation present
```

### UI Implementation (index.html)

The web UI includes teach mode controls (enter/exit, record, stop) and a custom
action list with play and rename.

### Backend Endpoints

Already defined in `web_server.py`:
- `POST /api/teach/record/start` - Start recording (API 7110)
- `POST /api/teach/record/stop` - Stop recording (API 7110)
- `POST /api/teach/rename` - Rename an action (API 7109)
- `GET /api/custom_action/robot_list` - Get custom + preset actions (API 7107)
- `POST /api/custom_action/execute` - Execute custom action (API 7108)
- `POST /api/custom_action/stop` - Stop playback (API 7113)

## FSM State Requirements for Teach Mode

From SDK documentation and code analysis:

## Error Codes for Teach Mode

From SDK documentation:

```python
ERROR_CODES = {
    0:    "Success",
    7400: "Action is occupied (already executing)",
    7401: "Arm is raised (position conflict)",
    7402: "Action ID does not exist",
    7404: "Invalid FSM state for gesture",
}
```

## Testing Workflow

### Manual Testing Steps (G1 Air)

1. **Get Action List (JSON API 7107)**
  ```json
  {"api_id":7107,"data":"","id":1,"priority":false,"topic":"rt/api/arm/request"}
  ```

2. **Start/Stop Recording (JSON API 7110)**
  - Start with a non-empty action name; stop with an empty action name

3. **Execute Custom Action (JSON API 7108)**
  ```json
  {"api_id":7108,"data":"{\"action_name\":\"my_wave\"}","id":2,"priority":false,"topic":"rt/api/arm/request"}
  ```

## References

### File Locations

| Resource | Location | Notes |
|----------|----------|-------|
| Python SDK | `../../sdk2_python/` | Reference implementation |
| C++ Examples | `../../unitree_docs/arm-control-routine.md` | Low-level control patterns |
| Web Controller | `../../g1_app/` | Production implementation |

### Documentation

- [Arm Control Routine](../../unitree_docs/arm-control-routine.md) - Low-level motion control
- [Sport Services Interface](../../unitree_docs/sport-services-interface.md) - FSM and motion APIs
- [Python SDK README](../../sdk2_python/README.md) - API quick reference
- [Phone Log Protocols](PROTOCOLS_FROM_PHONE_LOGS.md) - Primary evidence

### GitHub References

- [Unitree SDK2 Python](https://github.com/unitreerobotics/unitree_sdk2_python)
- [Unitree SDK2 C++](https://github.com/unitreerobotics/unitree_sdk2)

## Implementation Status

### ✅ Completed

- API reference documentation (7108, 7113, etc.)
- Python SDK missing API identification
- Web controller endpoints defined
- FSM state validation logic
- Error handling framework

### 🔄 In Progress

- Python SDK enhancement (adding teach mode methods)
- Android app protocol analysis
- Web UI teach mode workflow integration

### ⏳ Pending

- Validate teach mode on physical robot
- Stress test custom action recording/playback
- Optimize motion smoothness parameters
- Add gesture library management

## Next Steps

1. **Add Python SDK methods** - Use implementation guide above
2. **Test with robot** - Verify APIs 7107/7108/7109/7110/7113 work as documented
3. **Enhance web UI** - Full teach mode workflow in frontend
4. **Document differences** - G1 Air vs EDU teach mode support
5. **Create examples** - Sample code for teach mode workflows
