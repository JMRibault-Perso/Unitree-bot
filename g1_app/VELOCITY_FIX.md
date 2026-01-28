# Velocity Control Fix - 2026-01-25

## Problem
WASD keyboard controls stopped working after VelocityLimits constants were renamed.

## Root Cause
In `api/constants.py`, constants were renamed:
- `MAX_LINEAR` → `WALK_MAX_LINEAR` / `RUN_MAX_LINEAR`
- `MAX_STRAFE` → `WALK_MAX_STRAFE` / `RUN_MAX_STRAFE`
- `MAX_ANGULAR` → `WALK_MAX_ANGULAR` / `RUN_MAX_ANGULAR`

But `command_executor.py` line 85-87 still referenced the old `MAX_LINEAR/MAX_STRAFE/MAX_ANGULAR` names, causing:
```
AttributeError: type object 'VelocityLimits' has no attribute 'MAX_LINEAR'
```

## Fix Applied
Updated `command_executor.py` to use `WALK_MAX_LINEAR/STRAFE/ANGULAR`:
```python
ly_normalized = vx / VelocityLimits.WALK_MAX_LINEAR
lx_normalized = vy / VelocityLimits.WALK_MAX_STRAFE  
rx_normalized = omega / VelocityLimits.WALK_MAX_ANGULAR
```

## Behavior
Wireless controller normalization uses WALK mode maximums (1.0 m/s, 1.0 rad/s) as the baseline:

### WASD Commands:
- W/S (forward/back): ±0.3 m/s → ly = ±0.30
- A/D (strafe): ±0.2 m/s → lx = ±0.20
- Q/E (rotate): ±0.5 rad/s → rx = ±0.50

### Robot Interpretation by Mode:
**WALK mode (FSM 500/501):**
- ly=0.30 → 0.30 m/s forward (30% of 1.0 m/s max)

**RUN mode LOW (FSM 801, SpeedMode 0):**
- ly=0.30 → 0.30 m/s forward (30% of 1.0 m/s max)

**RUN mode HIGH (FSM 801, SpeedMode 2):**
- ly=0.30 → 0.81 m/s forward (30% of 2.7 m/s max)

**This is INTENTIONAL** - WASD keys are percentage-based, so they go faster in higher speed modes. This matches yesterday's working behavior.

## Alternative Approach Considered
Mode-aware normalization using `VelocityLimits.get_max_linear(fsm_state, speed_mode)` would give:
- Consistent absolute speeds (0.3 m/s always = 0.3 m/s)
- Requires passing FSM state to executor

This was NOT implemented because:
1. Yesterday's code used static MAX values (matching WALK mode)
2. Percentage-based behavior (faster in RUN) may be desired
3. Keeps backwards compatibility

## Test Results
See `test_velocity_normalization.py` for detailed analysis of both approaches.

## Files Modified
- `g1_app/core/command_executor.py` (lines 85-87)
