# Motion Control Tests

FSM (Finite State Machine) control, locomotion, and sport mode tests.

## 🗂️ Available Tests

### FSM Control
- `simple_control.py` - Interactive FSM command sender (DAMP, READY, BALANCE, SIT, etc.)
- `quick_control.py` - Quick preset motion commands
- `test_fsm_states.py` - Validate FSM state transitions

### Velocity Control
- `test_velocity.py` - Send velocity commands (vx, vy, vyaw)
- `test_movement_patterns.py` - Pre-programmed movement sequences

### Sport Mode
- `test_balance_modes.py` - Test different balance modes
- `test_gestures.py` - Trigger preset gestures (hello, sit, stand up)

## 🎮 FSM State Machine

```
ZERO_TORQUE (0) → DAMP (1001) → READY (1005) → LOCK_STAND/RUN
                                                     ↓
                                                BALANCE_STAND (1002)
                                                STAND_UP (1004)
                                                SIT (1009)
```

## 📝 Quick Commands

### Interactive Control
```bash
python3 simple_control.py
# Commands: d=damp, r=ready, b=balance, u=stand up, s=sit, h=hello
```

### Velocity Control
```bash
python3 test_velocity.py --vx 0.3 --vy 0.0 --vyaw 0.0
```

## 🚨 Safety Rules

- **ALWAYS** start with DAMP (1001) after power-on
- **NEVER** skip READY (1005) before locomotion
- **EMERGENCY**: Press Ctrl+C or send DAMP command
- **Sequence**: DAMP → READY → Motion commands

## 🔍 API Reference

| API ID | Command | Safety Level |
|--------|---------|--------------|
| 1001 | DAMP | ✅ Safe (zero torque) |
| 1005 | READY | ✅ Safe (standing ready) |
| 1002 | BALANCE_STAND | ⚠️ Requires READY |
| 1004 | STAND_UP | ⚠️ Requires READY |
| 1009 | SIT | ⚠️ Requires READY |
| 1016 | HELLO | ⚠️ Gesture (arm movement) |
| 7105 | SET_VELOCITY | ⚠️ Locomotion command |

## 🧪 Testing Sequence

1. Power on robot
2. Run `simple_control.py`
3. Send DAMP (d) - robot goes zero torque
4. Send READY (r) - robot stands
5. Send motion commands (b/u/s/h)
6. Always end with DAMP (d)
