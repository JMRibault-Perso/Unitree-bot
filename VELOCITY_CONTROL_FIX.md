# Velocity Control Fix

## Issue

Velocity control commands were being sent but robot wasn't moving, even though HTTP API returned success (200 OK).

## Root Cause

The `is_ready_for_motion()` function in [state_machine.py](g1_app/core/state_machine.py) was missing valid motion states. It only allowed:
- `START` (200) - Preparatory posture, **NOT a motion mode**
- `LOCK_STAND` (500) - Walk mode ✓

But it was **missing**:
- `LOCK_STAND_ADV` (501) - Walk mode with 3DOF waist control
- `RUN` (801) - Run mode (faster speeds)

According to [Unitree documentation](https://support.unitree.com/home/en/G1_developer/sport_services_interface), velocity commands work in these FSM states:

| FSM ID | Mode Name | Description |
|--------|-----------|-------------|
| 500 | Walk Motion | Basic walking with balance control |
| 501 | Walk Motion-3Dof-waist | Walking + 3DOF waist for motion recording |
| 801 | Run | Fast motion mode |

## Solution

### 1. Fixed Backend State Check

**File**: `g1_app/core/state_machine.py`

```python
def is_ready_for_motion(self) -> bool:
    """Check if robot is in a state that allows motion commands"""
    return self._current_state.fsm_state in [
        FSMState.LOCK_STAND,      # Walk mode (500)
        FSMState.LOCK_STAND_ADV,  # Walk mode with 3DOF waist (501)
        FSMState.RUN,             # Run mode (801)
    ]
```

**Changes**:
- ✅ Added `FSMState.RUN` (801)
- ✅ Added `FSMState.LOCK_STAND_ADV` (501)
- ✅ Removed `FSMState.START` (not a motion mode, just preparatory)

### 2. Updated Web UI State Check

**File**: `g1_app/ui/index.html`

```javascript
function isVelocityControlAvailable() {
    // Velocity control works in WALK (500), WALK-3DOF (501), and RUN (801) modes
    return currentFsmState === 'LOCK_STAND' || 
           currentFsmState === 'LOCK_STAND_ADV' ||
           currentFsmState === 'RUN';
}
```

**Changes**:
- ✅ Added check for `LOCK_STAND_ADV` (501)
- ✅ Simplified logic (removed unnecessary `FSM_STATES.find()` calls)

### 3. Updated User Messages

Warning banner now shows:
```
⚠️ Velocity control disabled: Robot must be in WALK (500), WALK-3DOF (501), or RUN (801) mode.
```

Error messages now mention all three valid states.

## How It Works

The existing architecture **already correctly wraps DDS commands using WebRTC**:

```
Web UI (JavaScript)
    ↓ HTTP POST /api/move
FastAPI Server (web_server.py)
    ↓ await robot.set_velocity()
RobotController (robot_controller.py)
    ↓ await self.executor.set_velocity()
CommandExecutor (command_executor.py)
    ↓ await datachannel.pub_sub.publish_request_new()
WebRTC DataChannel
    ↓ DDS-wrapped message
Robot (rt/api/sport/request topic)
    ↓ Executes SET_VELOCITY API (7105)
```

**Nothing was wrong with the WebRTC/DDS implementation** - it was just the motion state validation that was incomplete.

## Testing

1. Connect to robot via web UI
2. Transition to LOCK_STAND (500) or RUN (801) mode
3. Velocity controls should now work:
   - WASD/QE keyboard controls
   - On-screen directional buttons
   - Velocity scaling slider

## References

- [Unitree Sport Services Interface](https://support.unitree.com/home/en/G1_developer/sport_services_interface) - Official API documentation
- [FSM State Diagram](https://support.unitree.com/home/en/G1_developer/sport_services_interface#mode-switching) - Valid state transitions
- WebRTC Implementation: `/root/G1/go2_webrtc_connect` library
