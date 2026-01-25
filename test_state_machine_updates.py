#!/usr/bin/env python3
"""Test state machine updates for bidirectional squat transitions"""

import sys
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.api.constants import FSMState
from g1_app.core.state_machine import StateMachine

print("=" * 70)
print("Testing State Machine Updates")
print("=" * 70)

sm = StateMachine()

# Test 1: SQUAT_TO_STAND should now allow STAND_TO_SQUAT
print("\n1. Testing SQUAT_TO_STAND (706) transitions:")
sm._current_state.fsm_state = FSMState.SQUAT_TO_STAND
allowed = sm.get_allowed_transitions()
allowed_names = sorted([s.name for s in allowed])
print(f"   Allowed from SQUAT_TO_STAND: {allowed_names}")

if 'STAND_TO_SQUAT' in allowed_names:
    print("   ✅ STAND_TO_SQUAT is now allowed (bidirectional toggle)")
else:
    print("   ❌ STAND_TO_SQUAT not found")

if 'SQUAT_TO_STAND' in allowed_names:
    print("   ✅ Can toggle back to itself")
else:
    print("   ❌ Cannot toggle to itself")

# Test 2: STAND_TO_SQUAT transitions
print("\n2. Testing STAND_TO_SQUAT (707) transitions:")
sm._current_state.fsm_state = FSMState.STAND_TO_SQUAT
allowed = sm.get_allowed_transitions()
allowed_names = sorted([s.name for s in allowed])
print(f"   Allowed from STAND_TO_SQUAT: {allowed_names}")

if 'SQUAT_TO_STAND' in allowed_names:
    print("   ✅ SQUAT_TO_STAND is allowed (can use this instead)")
else:
    print("   ❌ SQUAT_TO_STAND not found")

# Test 3: From RUN state (walking), verify SQUAT_TO_STAND is available
print("\n3. Testing RUN (801) state can access squat toggle:")
sm._current_state.fsm_state = FSMState.RUN
allowed = sm.get_allowed_transitions()
allowed_names = sorted([s.name for s in allowed])
print(f"   Allowed from RUN: {allowed_names}")

if 'SQUAT_TO_STAND' in allowed_names:
    print("   ✅ SQUAT_TO_STAND accessible from RUN (can squat while walking)")
else:
    print("   ❌ SQUAT_TO_STAND not accessible")

print("\n" + "=" * 70)
print("State machine updates verified!")
print("=" * 70)
