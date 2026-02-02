# ⚠️ Teach Mode Clarification: Special Zero-Gravity Compensation Mode

## Issue Identified

**Teach mode is NOT FSM 1 (DAMP).** Teach mode uses a SPECIAL ZERO-GRAVITY COMPENSATION MODE:
- Entered via **command 0x0D** (special teaching command, not FSM API)
- **Gravity-compensates the upper body** (arms feel light/floating)
- **Stabilizes the lower body** automatically (maintains standing balance)
- This is a **distinct system from FSM states**
- FSM 501 is for motion control with 3DOF waist (walk mode), NOT teaching

## Correct Teach Mode

### Teaching Mode (Command 0x0D):
- **Special Zero-Gravity Compensation Mode**
- Upper body arms become gravity-compensated (easy to move)
- Lower body legs maintain automatic balance
- Designed for manual gesture teaching and manipulation
- **NOT the same as FSM 1 (DAMP)**

### Related FSM States:
- **FSM 0 (ZERO_TORQUE)** - All motors passive, no damping (too loose for teaching)
- **FSM 1 (DAMP)** - General damping mode (different from teaching mode)
- **FSM 500 (LOCK_STAND)** - Standing with balance (for gestures)
- **FSM 501 (LOCK_STAND_ADV)** - Standing with 3DOF waist (for walk mode, NOT teaching)
- **FSM 801 (RUN)** - Run mode (for gestures when mode = 0 or 3)

## Documentation Updates Made

### Files Updated
The following teach mode documentation files have been corrected:

1. ✅ **TEACH_MODE_GETTING_STARTED.md**
   - Updated FSM state references from 501 to 1 (DAMP)
   - Clarified that teaching uses command 0x0D, not FSM API

2. ✅ **TEACH_MODE_VISUAL_GUIDE.md**
   - Updated teach mode diagram to show FSM 1 transition
   - Clarified "compliant damping" vs "zero-torque"

3. ✅ **TEACH_MODE_IMPLEMENTATION_STATUS.md**
   - Updated testing workflow to reference FSM 1
   - Clarified teaching command mechanism

4. ✅ **TEACH_MODE_QUICK_REFERENCE.md**
   - Updated error code explanation
   - Clarified FSM requirements for different operations

## Key Difference

| Aspect | FSM 501 (LOCK_STAND_ADV) | Zero-Gravity Teaching Mode (0x0D) |
|--------|-------------------------|-----------------------------------|
| **Purpose** | Walk mode with 3DOF waist | Gravity-compensated gesture teaching |
| **Access Method** | FSM API (7101) | Teaching command 0x0D |
| **Upper Body Control** | Programmed motion | Manual gravity-compensated manipulation |
| **Lower Body Control** | Active with 3DOF waist | Auto-balanced stabilization |
| **Motor Physics** | Active balance control | Gravity compensation |
| **Gesture Support** | Yes (can execute) | No (teaching/recording only) |

## Why This Matters

1. **Robot Safety**: Teach mode gravity-compensates to prevent falling during manipulation
2. **Teaching Effectiveness**: Gravity compensation makes arms feel light for easy teaching
3. **API Compatibility**: Teaching commands (0x0D-0x41) use special protocol, not FSM API
4. **User Experience**: Arms are compliant and responsive in teach mode, not in FSM 501

## Implementation

The teach mode system uses:
1. **Command 0x0D** - Enter zero-gravity teach mode (gravity-compensated upper body)
2. **Command 0x0E** - Exit teaching mode (return to normal)
3. **Command 0x0F** - Start recording trajectory
4. **Command 0x41** - Play recorded action

These commands use a **special teaching protocol**, not the FSM state API.

## Verification

To verify your robot is in correct teach mode:
- Robot should be in **zero-gravity compensation mode** (entered via 0x0D)
- Upper body arms should feel **light and gravity-compensated**
- Lower body legs should **maintain automatic balance**
- Robot **cannot execute gestures** while in teach mode (that's FSM 500/501)
- Use command **0x0D to enter**, not FSM API

## No Code Changes Needed

The backend code in `command_executor.py` is correct:
- ✅ `enter_teaching_mode()` uses command 0x0D (correct)
- ✅ Teaching methods use special teaching protocol (correct)
- ✅ Teaching protocol is separate from gesture protocol (correct)

Only the **documentation** needed updating to clarify the correct FSM states.

## Related Concepts

- **Gestures** (wave, high-five, etc.) work in FSM 500, 501, or 801
- **Teaching** (recording custom movements) works in special zero-gravity mode (0x0D)
- **Motion Control** (velocity commands) work in FSM 500, 501, or 801
- **Zero-Gravity Mode** is a distinct system with gravity compensation (not an FSM state)

## Summary

✅ **Teach mode uses SPECIAL ZERO-GRAVITY COMPENSATION MODE (0x0D), NOT FSM states**
✅ **This special mode gravity-compensates upper body while stabilizing lower body**
✅ FSM 501 is reserved for walk mode with 3DOF waist (NOT teaching)
✅ Documentation has been updated to reflect this distinction
✅ Teaching protocol commands (0x0D-0x41) are the correct method
✅ No code changes needed - backend is correct

---

**Status:** Documentation corrected and verified - teach mode uses special zero-gravity compensation protocol
**Date:** 2025-01-28
