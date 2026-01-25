# G1 FSM States - Complete Reference

**Source**: [Unitree Official Documentation](https://support.unitree.com/home/en/G1_developer/sport_services_interface#Expert%20interface)

## State Classification

### Stable States (Final Destinations)
These are endpoint states where the robot settles after completing an action. **UI buttons re-enable only when the robot reaches and stays in one of these states for 2+ consecutive messages.**

| FSM ID | Name          | Balance | Description                    | UI Re-enable |
| ------ | ------------- | ------- | ------------------------------ | ------------ |
| 0      | ZERO_TORQUE   | No      | Motors off, no damping         | ✅ Yes       |
| 1      | DAMP          | No      | Safe damping mode (orange LED) | ✅ Yes       |
| 200    | START         | Yes     | Ready/standing mode (blue LED) | ✅ Yes       |
| 500    | LOCK_STAND    | Yes     | Walk mode (~1.0 m/s)           | ✅ Yes       |
| 501    | LOCK_STANDING | Yes     | Walk mode + 3DOF waist         | ✅ Yes       |
| 801    | RUN           | Yes     | Run mode (up to 3.0 m/s)       | ✅ Yes       |

### Transitional States (Pass-Through)
These are intermediate states the robot passes through during actions. **UI buttons remain disabled when in these states.**

| FSM ID | Name           | Type     | Description                  | UI Behavior                      |
| ------ | -------------- | -------- | ---------------------------- | -------------------------------- |
| 2      | SQUAT          | Position | Squat position               | ⏳ Transitional                   |
| 3      | SIT            | Position | Seated mode (green LED)      | ⏳ Transitional                   |
| 4      | LOCK_STANDING  | Position | Standing without balance     | ⏳ Transitional                   |
| 702    | STAND_UP       | Action   | Stand up from lying position | ⏳ Action (not tracked as target) |
| 706    | SQUAT_TO_STAND | Action   | Squat/stand toggle           | ⏳ Action (not tracked as target) |

**Note**: States 702 (STAND_UP) and 706 (SQUAT_TO_STAND) are **action triggers**, not destination states. Clicking these buttons initiates a transition that ends in a stable state (typically DAMP or RUN).

## UI Safety Logic

The web interface uses **state-driven button control** to prevent accidental commands during robot motion:

1. **Button clicked** → All buttons disabled, `targetState` set (or `null` for action states 702/706)
2. **Robot transitions** → Passes through intermediate states (SQUAT_TO_STAND, SIT, etc.)
3. **Reaches stable state** → Waits for 2 consecutive identical state reports
4. **Buttons re-enable** → Only when stable state confirmed

**Example**: Clicking "SQUAT UP" (706):
```
User clicks SQUAT UP (706) → Buttons disabled
Robot: DAMP → SQUAT_TO_STAND → RUN
RUN received twice → Buttons re-enable ✅
```

## Complete FSM State Table

| FSM ID  | Name                       | Balance Control | Description                                   |
| ------- | -------------------------- | --------------- | --------------------------------------------- |
| 0       | Zero Torque                | No              | Motors off, no damping                        |
| 1       | Damping                    | No              | Safe damping mode (orange LED)                |
| 2       | Position Control Squat     | No              | Squat position                                |
| 3       | Position Control Sit Down  | No              | Seated mode (green LED)                       |
| 4       | Lock Standing              | No              | Standing without balance                      |
| 200     | START                      | Yes             | Ready/standing mode (blue LED)                |
| **500** | **Walk Motion**            | Yes             | **Walk mode (~1.0 m/s)**                      |
| **501** | **Walk Motion Advanced**   | Yes             | **Walk mode + 3DOF waist (motion recording)** |
| 702     | Lie Down, Stand Up         | Yes             | Stand up from lying position                  |
| 706     | Balance Squat, Squat Stand | Yes             | Squat/stand toggle (recovery)                 |
| **801** | **Run**                    | Yes             | **Run mode (up to 3.0 m/s)**                  |

## Speed Control (RUN mode only)

When in RUN mode (FSM 801), you can set maximum speed via `SetSpeedMode(mode)`:

| Mode | Max Speed |
| ---- | --------- |
| 0    | 1.0 m/s   |
| 1    | 2.0 m/s   |
| 2    | 2.7 m/s   |
| 3    | 3.0 m/s   |

## State Transitions

### From RUN (801)
- → **LOCK_STAND (500)** - Slow down to walk mode
- → **SIT (3)** - Sit down
- → **SQUAT_TO_STAND (706)** - Squat toggle
- → **DAMP (1)** - Emergency stop

### From LOCK_STAND (500) - Walk Mode
- → **RUN (801)** - Speed up to run mode
- → **SIT (3)** - Sit down
- → **SQUAT_TO_STAND (706)** - Squat toggle
- → **DAMP (1)** - Emergency stop

### From DAMP (1) - Safe Mode
- → **ZERO_TORQUE (0)** - Turn off motors
- → **START (200)** - Get ready to walk/run
- → **SIT (3)** - Sit down
- → **SQUAT (2)** - Go to squat position
- → **SQUAT_TO_STAND (706)** - Squat/stand toggle
- → **STAND_UP (702)** - Stand up from lying

## FSM Mode (within states)

The `fsm_mode` field indicates sub-modes within certain FSM states:

### In RUN mode (801):
- **fsm_mode = 0**: Standing state, arm actions allowed
- **fsm_mode = 3**: Moving state, arm actions allowed
- **fsm_mode = 1**: Moving state, arm actions NOT allowed

### In LOCK_STAND (500) or LOCK_STAND_ADV (501):
- **fsm_mode = 0**: Standing state
- **fsm_mode = 1**: Moving state

## Current Robot Status

**Your robot is currently in:**
- **FSM State**: 801 (RUN)
- **FSM Mode**: 0 (standing, arm actions allowed)
- **Task ID**: 4

This means the robot is in RUN mode but currently standing still. You can:
1. Send velocity commands to make it run
2. Slow down to LOCK_STAND (500) for walk mode
3. Stop with DAMP (1) for safety

## Velocity Control

### In RUN or WALK modes:
```python
# SetVelocity(vx, vy, omega, duration)
# vx: forward speed (m/s)
# vy: sideways speed (m/s)  
# omega: rotation speed (rad/s)
# duration: how long command is valid (seconds)

# Example: Move forward at 1.5 m/s
client.SetVelocity(1.5, 0.0, 0.0, 1.0)

# Example: Turn in place
client.SetVelocity(0.0, 0.0, 0.5, 1.0)

# Example: Continuous movement
client.SetVelocity(1.0, 0.0, 0.0, 0.0)  # duration=0 means continuous
```

## Service Modes

The robot also has different "service modes" that affect which FSM states are available:

- **sport_mode** (normal): Standard locomotion
- **ai_sport**: AI-enhanced locomotion
- **advanced_sport**: Advanced control features

These are separate from FSM states and are switched via `MotionSwitcherClient`.

## Important Notes

1. **RUN vs WALK**: RUN (801) is faster than WALK (500), but both support velocity control
2. **3DOF Waist**: LOCK_STAND_ADV (501) adds waist articulation and is **only accessible via motion recording mode**, not directly commandable
3. **Arm Actions**: In RUN mode (801) with fsm_mode ∈ {0, 3}, arm gesture commands are supported
4. **Safety**: Always use DAMP (1) for emergency stops, not ZERO_TORQUE (0)
5. **Balance Control**: States with balance control (500, 501, 801) actively maintain posture
6. **Motion Recording**: State 501 is entered automatically when robot plays back recorded motions that use 3DOF waist
