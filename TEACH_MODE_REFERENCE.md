# Teach Mode Implementation - Complete Reference

## Overview

This document consolidates all teach mode information from the codebase, SDKs, and decompiled Android app to provide a complete implementation guide.

## API Reference

### Teach Mode APIs (7108-7113)

Located in SDK but **not fully exposed in Python wrapper**:

| API ID | Service | Method | Parameters | Return | Status |
|--------|---------|--------|------------|--------|--------|
| 7107 | arm | GetActionList | None | Array of {id, name} | ✅ Python SDK |
| 7108 | arm | ExecuteCustomAction | action_name (string) | error_code | ⚠️ C++ only |
| 7109 | arm | RecordCustomAction | action_name (string) | error_code | ⚠️ C++ only |
| 7110 | arm | DeleteCustomAction | action_name (string) | error_code | ⚠️ C++ only |
| 7111 | arm | GetCustomActionList | None | Array of action_name | ⚠️ C++ only |
| 7112 | arm | ClearCustomActions | None | error_code | ⚠️ C++ only |
| 7113 | arm | StopCustomAction | None | error_code | ⚠️ C++ only |

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

## Python SDK - Custom Action Implementation

To add teach mode support to Python SDK, modify:

### 1. Add API IDs to `sdk2_python/unitree_sdk2py/g1/arm/g1_arm_action_api.py`

```python
# Add to existing definitions
ROBOT_API_ID_ARM_ACTION_EXECUTE_CUSTOM_ACTION = 7108
ROBOT_API_ID_ARM_ACTION_STOP_CUSTOM_ACTION = 7113
ROBOT_API_ID_ARM_ACTION_GET_ACTION_LIST_CUSTOM = 7111
ROBOT_API_ID_ARM_ACTION_RECORD_ACTION = 7109
ROBOT_API_ID_ARM_ACTION_DELETE_ACTION = 7110
ROBOT_API_ID_ARM_ACTION_CLEAR_ACTIONS = 7112
```

### 2. Add Methods to `sdk2_python/unitree_sdk2py/g1/arm/g1_arm_action_client.py`

```python
def ExecuteCustomAction(self, action_name: str):
    """Execute a custom taught action
    
    Args:
        action_name (str): Name of the custom action to execute
        
    Returns:
        int: Error code (0 = success)
    """
    p = {}
    p["data"] = action_name
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_EXECUTE_CUSTOM_ACTION, parameter)
    return code

def StopCustomAction(self):
    """Stop executing custom action (emergency stop)
    
    Returns:
        int: Error code (0 = success)
    """
    p = {}
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_STOP_CUSTOM_ACTION, parameter)
    return code

def GetCustomActionList(self):
    """Get list of all custom taught actions
    
    Returns:
        tuple: (error_code, list of action names)
    """
    p = {}
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_GET_ACTION_LIST_CUSTOM, parameter)
    if code == 0:
        return code, json.loads(data)
    else:
        return code, None

def RecordCustomAction(self, action_name: str):
    """Start recording a new custom action (teach mode entry)
    
    Args:
        action_name (str): Name for the new action
        
    Returns:
        int: Error code (0 = success)
    """
    p = {}
    p["data"] = action_name
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_RECORD_ACTION, parameter)
    return code

def DeleteCustomAction(self, action_name: str):
    """Delete a custom taught action
    
    Args:
        action_name (str): Name of action to delete
        
    Returns:
        int: Error code (0 = success)
    """
    p = {}
    p["data"] = action_name
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_DELETE_ACTION, parameter)
    return code

def ClearCustomActions(self):
    """Clear all custom taught actions
    
    Returns:
        int: Error code (0 = success)
    """
    p = {}
    parameter = json.dumps(p)
    code, data = self._Call(ROBOT_API_ID_ARM_ACTION_CLEAR_ACTIONS, parameter)
    return code
```

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

The web UI has teach mode buttons but needs integration:
- "🎓 Enter Teach Mode" - Start recording
- "⏹️ Stop Recording" - Finish recording
- Custom actions list - Shows taught actions

### Backend Endpoints

Already defined in `web_server.py`:
- `POST /api/teach/record?action_name=<name>` - Start recording
- `POST /api/teach/stop` - Stop recording  
- `GET /api/teach/list` - Get custom actions
- `POST /api/gesture/<action_name>` - Execute custom action
- `POST /api/gesture/stop` - Stop action

## FSM State Requirements for Teach Mode

From SDK documentation and code analysis:

### Valid Teach Mode States

Custom actions can be executed in specific FSM states:

```python
# From FSM state machine analysis
TEACH_MODE_VALID_STATES = {
    500,    # Gesture state (always valid)
    501,    # Extended gesture state
    801     # Custom mode (requires mode 0 or 3)
}

# FSM Mode requirements
TEACH_MODE_VALID_MODES = {
    0,      # Normal mode
    3       # Advanced mode
}
```

### State Transition for Teach Mode Entry

```python
# To enter teach recording:
1. Call enter_teaching_mode() or click "Enter Damping Mode"
2. Robot enters special zero-gravity compensation mode (command 0x0D)
3. Upper body arms become gravity-compensated (feel light)
4. Lower body legs maintain automatic balance
5. Call start_recording() or click "Start Record"
6. Perform desired motion by manually moving robot
7. Call stop_recording() or click "Stop Record"
8. Action is automatically saved to robot

# To execute custom action:
1. Ensure robot in LOCK_STAND (FSM 500/501) or RUN (FSM 801)
2. Call ExecuteCustomAction(action_name)  # API 7108
3. Robot performs recorded motion
4. Motion completes or StopCustomAction() is called
```

## Protocol Analysis (From Decompiled Android App)

From `android_app_decompiled/` investigation:

### Discovery in Decompiled Code

Look in `Unitree_Explore/smali*/` for:
- Classes with "TeachMode", "RecordMode", "CustomAction"
- HTTP/WebSocket endpoints for teach mode
- Motion recording/playback mechanics
- UI flow for gesture recording

### Search Patterns

```bash
# Find teach mode implementation
grep -r "teach\|record.*action\|custom.*action" \
  android_app_decompiled/Unitree_Explore/smali*/

# Find motion recording
grep -r "record\|replay\|playback" \
  android_app_decompiled/Unitree_Explore/smali*/

# Find gesture state machine
grep -r "FSM.*500\|GESTURE\|action.*state" \
  android_app_decompiled/Unitree_Explore/smali*/
```

## Error Codes for Teach Mode

From SDK documentation:

```python
ERROR_CODES = {
    0:    "Success",
    7400: "Action is occupied (already executing)",
    7401: "Arm is raised (position conflict)",
    7402: "Unknown error",
    7403: "Teach mode not available",
    7404: "Invalid FSM state for gesture",
    7405: "Action not found",
    7406: "Storage full",
    7407: "Invalid action name",
}
```

## Testing Workflow

### Manual Testing Steps

1. **Setup**
   ```python
   client = G1ArmActionClient()
   client.Init()
   ```

2. **Get Custom Actions**
   ```python
   code, custom_actions = client.GetCustomActionList()
   print(f"Custom actions: {custom_actions}")
   ```

3. **Record New Action**
   ```python
   code = client.RecordCustomAction("my_wave")
   # Wait for user to perform motion (typically 10-30 seconds)
   # Motion is being recorded...
   code = client.StopCustomAction()
   ```

4. **Execute Custom Action**
   ```python
   code = client.ExecuteCustomAction("my_wave")
   # Robot performs recorded motion
   ```

5. **Delete Action**
   ```python
   code = client.DeleteCustomAction("my_wave")
   ```

## References

### File Locations

| Resource | Location | Notes |
|----------|----------|-------|
| Python SDK | `sdk2_python/` | Reference implementation |
| C++ Examples | `unitree_docs/arm-control-routine.md` | Low-level control patterns |
| Android App | `android_app_decompiled/` | Protocol reverse-engineering |
| Web Controller | `g1_app/` | Production implementation |

### Documentation

- [Arm Control Routine](unitree_docs/arm-control-routine.md) - Low-level motion control
- [Sport Services Interface](unitree_docs/sport-services-interface.md) - FSM and motion APIs
- [Python SDK README](sdk2_python/README.md) - API quick reference
- [Teaching Mode Protocol](TEACHING_MODE_PROTOCOL_COMPLETE.md) - Full protocol analysis

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
2. **Test with robot** - Verify APIs 7108-7113 work as documented
3. **Enhance web UI** - Full teach mode workflow in frontend
4. **Document differences** - G1 Air vs EDU teach mode support
5. **Create examples** - Sample code for teach mode workflows
