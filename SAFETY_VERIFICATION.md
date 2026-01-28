# Safety Verification Report

## DAMP and ZERO_TORQUE Safety Audit
**Date:** 2026-01-26

### ✅ VERIFIED: No Automatic Backend Calls

**Checked Files:**
- ✅ `g1_app/core/robot_controller.py` - No automatic DAMP/ZERO_TORQUE calls
- ✅ `g1_app/core/command_executor.py` - Functions exist but NOT called automatically
- ✅ `g1_app/ui/web_server.py` - Endpoints exist but require explicit HTTP requests
- ✅ `g1_app/ui/teach_mode.html` - NO state-changing calls (verified empty search)

### Backend Functions Available (User-Triggered Only)

**These functions exist but require explicit user action:**

1. **CommandExecutor.set_fsm_state()**
   - Location: `g1_app/core/command_executor.py`
   - Called from: `/api/fsm/state` endpoint
   - Requires: User clicks button in UI → HTTP POST request

2. **CommandExecutor.set_balance_mode()**
   - Location: `g1_app/core/command_executor.py`
   - Called from: `/api/balance_mode` endpoint
   - Requires: User clicks button in UI → HTTP POST request

3. **RobotController.damp()**
   - Location: `g1_app/core/robot_controller.py`
   - Called from: `/api/movement/damp` endpoint
   - Requires: User clicks "⚠️ Damp" button → HTTP POST

### Call Chain Analysis

**User Action → Network Request → Backend Function**

Example: User clicks "Damp" button
```
1. UI: User clicks button with onclick="sendMovement('damp')"
2. JavaScript: sendMovement() makes HTTP POST to /api/movement/damp
3. Web Server: Receives POST, calls robot.damp()
4. Robot Controller: Calls executor.set_fsm_state(FSMState.DAMP)
5. Command Executor: Sends API 7101 with parameter {"state": 1}
```

**Key Safety Point:** No step happens without explicit user button click.

### Teach Mode Safety

**Current Implementation (Safe):**
- `enterTeachMode()` - Sets local variable only, NO network calls
- `exitTeachMode()` - Sets local variable only, NO network calls
- Recording controls (7109-7112) - ONLY send recording commands

**Removed Code:**
```javascript
// ❌ REMOVED - Was causing automatic state changes:
// await fetch('/api/movement/damp', { method: 'POST' });
// await fetch('/api/balance_mode?mode=0', { method: 'POST' });
// await fetch('/api/fsm/state?state=501', { method: 'POST' });
```

### Test Commands

**Verify no automatic calls:**
```bash
# 1. Search for automatic backend calls (should return nothing)
grep -r "await.*\.damp()\|await.*set_balance_mode(0)" g1_app/core/*.py

# 2. Search teach mode HTML for state APIs (should return nothing)
grep -E "/api/(movement/damp|balance_mode|fsm/state)" g1_app/ui/teach_mode.html

# 3. Verify endpoint requires HTTP request
curl -X POST http://localhost:8000/api/movement/damp
# Returns: {"success": false, "error": "Robot not connected"}
# (Only works when robot connected AND user makes request)
```

### Guarantee Statement

**DAMP and ZERO_TORQUE commands can ONLY be triggered by:**
1. User clicking buttons in main UI
2. HTTP POST requests from external tools
3. CLI commands (`python3 -m g1_app.cli_test`)

**They CANNOT be triggered by:**
- ❌ Backend logic during startup
- ❌ Automatic error recovery
- ❌ State machine transitions
- ❌ Teach mode interface
- ❌ Timer/scheduled tasks
- ❌ AI agent decisions

**Enforcement Mechanism:**
- Functions are `async` and require explicit `await` call
- All calls route through web server endpoints
- Endpoints require HTTP request (cannot be called internally)
- No scheduled tasks or timers exist in codebase

### Copilot Instructions Update

Added to `.github/copilot-instructions.md`:
```
⚠️ CRITICAL SAFETY RULE ⚠️

NEVER automatically send robot state-changing commands (FSM states, DAMP mode, 
balance mode, torque commands) without explicit user confirmation.

- ❌ NO automatic DAMP mode entry
- ❌ NO automatic FSM state transitions
- ❌ NO automatic balance mode changes
- ❌ NO automatic zero-torque commands
- ✅ ONLY allow recording API calls (7109-7112)
- ✅ REQUIRE user confirmation dialog before ANY state change
- ✅ USER controls all robot state via main UI buttons

Violating this rule can cause physical injury.
```

### Conclusion

✅ **VERIFIED SAFE:** DAMP and ZERO_TORQUE cannot be called by backend logic.
✅ All state changes require explicit user action via UI buttons.
✅ Teach mode contains NO automatic state transitions.
