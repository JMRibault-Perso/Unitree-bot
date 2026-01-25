# Velocity Control - The Real Fix

## The Actual Problem

The velocity commands were using **API 7105 (SET_VELOCITY)** from the expert interface, but the **Android app uses `rt/wirelesscontroller` topic** with joystick emulation instead.

### What Was Wrong

**File**: `g1_app/core/command_executor.py` - `set_velocity()` function

```python
# WRONG - This is what the code was doing:
payload = {
    "api_id": LocoAPI.SET_VELOCITY,  # API 7105
    "parameter": json.dumps({
        "velocity": [vx, vy, omega],
        "duration": duration
    })
}
await self._send_command(payload)  # Sends to rt/api/sport/request
```

This sends velocity via the **sport API service**, which may not work for WiFi-connected robots or may require different FSM states.

### What the Android App Actually Does

From examining `/root/G1/go2_webrtc_connect/examples/g1/data_channel/sport_mode/sportmode.py`:

```python
# CORRECT - This is what the Android app does:
conn.datachannel.pub_sub.publish_without_callback(
    "rt/wirelesscontroller",  # Wireless controller topic (joystick emulation)
    {
        "lx": 0.0,   # Strafe left/right
        "ly": 0.0,   # Forward/backward
        "rx": 1.0,   # Rotation
        "ry": 0.0,   # Unused
        "keys": 0    # No key presses
    }
)
```

### The Fix

**File**: `g1_app/core/command_executor.py`

```python
async def set_velocity(self, vx: float = 0.0, vy: float = 0.0, omega: float = 0.0,
                 duration: float = 1.0, continuous: bool = False) -> dict:
    """
    Set robot velocity using wireless controller topic (joystick emulation)
    
    This is how the Android app controls the robot - via rt/wirelesscontroller topic
    NOT via API 7105 (SET_VELOCITY)
    """
    # Apply safety limits
    vx = max(-VelocityLimits.MAX_LINEAR, min(VelocityLimits.MAX_LINEAR, vx))
    vy = max(-VelocityLimits.MAX_STRAFE, min(VelocityLimits.MAX_STRAFE, vy))
    omega = max(-VelocityLimits.MAX_ANGULAR, min(VelocityLimits.MAX_ANGULAR, omega))
    
    # Wireless controller uses joystick mapping:
    # ly = forward/back (was vx)
    # lx = strafe left/right (was vy)  
    # rx = rotation (was omega)
    payload = {
        "lx": vy,      # Strafe
        "ly": vx,      # Forward/back
        "rx": omega,   # Rotation
        "ry": 0.0,     # Unused
        "keys": 0      # No key presses
    }
    
    # Send via wireless controller topic (not API request)
    self.datachannel.pub_sub.publish_without_callback(
        "rt/wirelesscontroller",
        payload
    )
    
    return payload
```

## Key Differences

| Aspect | OLD (API 7105) | NEW (Wireless Controller) |
|--------|----------------|---------------------------|
| **Topic** | `rt/api/sport/request` | `rt/wirelesscontroller` |
| **Method** | `publish_request_new()` (waits for response) | `publish_without_callback()` (fire and forget) |
| **Format** | API call with parameters | Direct joystick values |
| **Coordinates** | `velocity: [vx, vy, omega]` | `{lx, ly, rx, ry, keys}` |
| **Duration** | Requires duration parameter | Continuous (no timeout) |
| **Used By** | SDK examples (wired/Jetson) | Android app (WiFi/WebRTC) |

## Why This Matters

1. **WiFi vs Wired**: The API 7105 approach may be designed for wired SDK connections (Ethernet to Jetson NX), while the wireless controller topic is specifically for remote control (like the Android app over WiFi)

2. **Response Handling**: API calls expect responses and may time out, wireless controller is fire-and-forget (like a real joystick)

3. **FSM State Requirements**: The wireless controller topic may work in more FSM states than the velocity API

## Testing

1. Connect robot via web UI
2. Switch to LOCK_STAND (500) or RUN (801) mode
3. Use WASD/directional buttons
4. Robot should now move using the same method as the Android app

## References

- Example code: `/root/G1/go2_webrtc_connect/examples/g1/data_channel/sport_mode/sportmode.py`
- Wireless controller topic: `rt/wirelesscontroller`
- Joystick mapping: lx (strafe), ly (forward), rx (yaw), ry (unused), keys (button presses)
