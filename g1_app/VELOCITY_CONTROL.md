# Velocity Control Implementation

## Overview
Added keyboard and button-based velocity control to the G1 robot web interface. This allows real-time movement control using WASD keys or on-screen directional buttons.

## Features

### 1. **Velocity Control Panel**
- **Location**: Displayed below FSM State Machine panel when connected to robot
- **3x3 Button Grid** for directional control:
  ```
  [      ] [ ⬆️ FWD ] [      ]
  [ ⬅️ LEFT] [ ⏹️ STOP] [➡️ RIGHT]
  [↶ TURN ] [⬇️ BACK] [TURN ↷]
  ```

### 2. **Keyboard Controls**
- **W**: Forward (vx = 0.3 m/s)
- **A**: Strafe Left (vy = 0.2 m/s)
- **S**: Backward (vx = -0.3 m/s)
- **D**: Strafe Right (vy = -0.2 m/s)
- **Q**: Turn Left (omega = 0.5 rad/s)
- **E**: Turn Right (omega = -0.5 rad/s)
- **Space**: Emergency Stop (all velocities = 0)

### 3. **Multi-Key Support**
- Press multiple keys simultaneously to combine movements
- Example: W + D = Forward + Strafe Right
- Example: W + Q = Forward + Turn Left
- Releasing any key recalculates velocity from remaining active keys

### 4. **Visual Feedback**
- **Current Velocity Display**: Shows real-time vx, vy, omega values
- **Button Styling**: 
  - Purple gradient for directional buttons
  - Red gradient for STOP button
  - Hover effects with shadows
  - Active state animation (pulse effect)

### 5. **Safety Features**
- Panel only visible when connected to robot
- All movement commands check connection state
- Displays error message if movement attempted while disconnected
- Velocity resets to 0 when disconnecting from robot
- Active keys cleared on disconnect

## Technical Implementation

### Backend (web_server.py)
```python
@app.post("/api/move")
async def move_robot(vx: float = 0, vy: float = 0, omega: float = 0):
    """Send velocity command to robot"""
    if not robot.is_connected:
        return {"success": False, "error": "Robot not connected"}
    
    await robot.set_velocity(vx, vy, omega)
    return {"success": True}
```

### Frontend (index.html)

#### JavaScript Functions
- `moveRobot(vx, vy, omega)`: Send velocity command via POST /api/move
- `stopRobot()`: Immediately stop all movement
- `updateVelocityDisplay()`: Update displayed velocity values
- `updateButtonStates()`: Visual feedback for active buttons

#### Keyboard Event Handlers
- `keydown`: Add key to active set, combine velocities, send command
- `keyup`: Remove key from active set, recalculate velocities
- Space bar preventDefault to avoid page scroll

#### CSS Styling
- `.velocity-btn`: Purple gradient with hover/active effects
- `.velocity-btn.stop-btn`: Red gradient for stop button
- `.velocity-btn.active`: Green glow with pulse animation
- `@keyframes pulse`: Pulsing shadow effect for active state

## Usage Instructions

### Prerequisites
- Robot must be in **WALK (500)** or **RUN (801)** mode for velocity control
- Use FSM State Machine panel to transition to appropriate mode first

### Movement Steps
1. **Connect to Robot**: Click "Connect" button in Bound Robots panel
2. **Enter WALK/RUN Mode**: 
   - From DAMP → Click "WALK" or "RUN"
   - From START → Click "WALK" or "RUN"
3. **Control Movement**:
   - **Buttons**: Click directional buttons for predefined velocities
   - **Keyboard**: Use WASD/QE keys for movement, Space to stop
   - **Combine**: Hold multiple keys for diagonal/turning movement
4. **Emergency Stop**: Press Space bar or click STOP button

### Example Movement Patterns
- **Forward Walk**: Press W
- **Diagonal Forward-Right**: Press W + D
- **Turn in Place**: Press Q or E
- **Circle**: Press W + Q (forward + turn left)
- **Strafe Right**: Press D
- **Stop**: Press Space

## API Reference

### POST /api/move
Send velocity command to robot.

**Parameters:**
- `vx` (float): Forward velocity in m/s [-0.3 to 0.3]
- `vy` (float): Strafe velocity in m/s [-0.2 to 0.2]
- `omega` (float): Yaw rotation in rad/s [-0.5 to 0.5]

**Response:**
```json
{
  "success": true
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Robot not connected"
}
```

## Velocity Ranges (from SDK examples)

Based on `g1_loco_client_example.cpp`:
- **vx (forward/backward)**: -0.5 to 0.5 m/s (UI uses ±0.3 for safety)
- **vy (strafe left/right)**: -0.3 to 0.3 m/s (UI uses ±0.2)
- **omega (yaw rotation)**: -1.0 to 1.0 rad/s (UI uses ±0.5)

Conservative values chosen for safety and stability during manual control.

## Connection to Robot Controller

The velocity commands flow through the existing robot controller infrastructure:

```
UI Button/Key → POST /api/move → robot.set_velocity() → executor.set_velocity() → SDK LocoClient.Move()
```

No changes required to `robot_controller.py` - the `set_velocity()` method was already implemented.

## File Changes

### Modified Files
1. **g1_app/ui/web_server.py**
   - Added POST /api/move endpoint

2. **g1_app/ui/index.html**
   - Added velocity control panel HTML
   - Added CSS for velocity buttons
   - Added JavaScript functions (moveRobot, stopRobot, updateVelocityDisplay)
   - Added keyboard event handlers (keydown, keyup)
   - Updated connectToRobot() to show velocity panel
   - Updated disconnect() to hide velocity panel and reset state

### No Changes Required
- **g1_app/core/robot_controller.py**: Already had `set_velocity()` method
- **g1_app/core/command_executor.py**: Already had velocity control logic
- Backend infrastructure was already complete

## Testing

### Manual Testing Steps
1. Start web server: `python3 ui/web_server.py`
2. Open browser: http://localhost:8000
3. Connect to robot
4. Transition to WALK or RUN mode via FSM panel
5. Test keyboard controls (WASD/QE/Space)
6. Test button controls (click directional buttons)
7. Test multi-key combinations
8. Verify velocity display updates
9. Test disconnect (panel should hide, velocity reset)

### Expected Behavior
- ✅ Velocity panel visible when connected
- ✅ Velocity panel hidden when disconnected
- ✅ Keyboard controls work in WALK/RUN modes
- ✅ Button controls work in WALK/RUN modes
- ✅ Multi-key combinations combine velocities
- ✅ Space bar stops immediately
- ✅ Velocity display updates in real-time
- ✅ Error message if movement attempted while disconnected
- ✅ Velocity resets to 0 on disconnect

## Future Enhancements

### Possible Improvements
1. **Joystick Support**: Add on-screen virtual joystick for analog control
2. **Velocity Presets**: Configurable speed profiles (slow/medium/fast)
3. **Gamepad Support**: USB gamepad/controller support via Gamepad API
4. **Visual Indicators**: Show active direction arrows on screen
5. **Acceleration Ramping**: Smooth velocity transitions instead of instant changes
6. **Safety Limits**: FSM state validation before accepting velocity commands
7. **Velocity Logging**: Record movement history for debugging
8. **Touch Controls**: Mobile-friendly touch/swipe controls

### SDK Integration
- Current implementation uses high-level `LocoClient.Move()` from SDK
- For more advanced control, could use low-level motor commands
- See `example/g1/low_level/` for direct motor control examples

## Notes

- Velocity values are conservative for safety during manual control
- SDK supports higher velocities - adjust `keyMap` values if needed
- Robot must be in appropriate FSM state (WALK/RUN) for movement
- Commands are sent continuously while keys held (not just on keydown)
- Connection state is user-driven - velocity panel shows/hides with connect/disconnect
