#!/usr/bin/env python3
"""
Simple Unit Tests for State Machine Bug
Tests that get_allowed_transitions() works correctly
"""

import sys
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.api.constants import FSMState
from g1_app.core.state_machine import StateMachine


def test_state_machine_zero_torque():
    """Test ZERO_TORQUE state transitions"""
    sm = StateMachine()
    
    # Start in ZERO_TORQUE (initial state)
    assert sm._current_state.fsm_state == FSMState.ZERO_TORQUE
    
    # Get allowed transitions for ZERO_TORQUE
    allowed = sm.get_allowed_transitions()
    print(f"\n ZERO_TORQUE allows: {[s.name for s in allowed]}")
    
    # ZERO_TORQUE should only allow ZERO_TORQUE and DAMP
    assert FSMState.ZERO_TORQUE in allowed
    assert FSMState.DAMP in allowed
    
    # Should NOT include START, SQUAT, etc.
    assert FSMState.START not in allowed, "ZERO_TORQUE should NOT allow START"
    assert FSMState.SQUAT not in allowed, "ZERO_TORQUE should NOT allow SQUAT"
    print("✓ ZERO_TORQUE transitions correct")


def test_state_machine_damp():
    """Test DAMP state transitions - THIS WAS THE BUG"""
    sm = StateMachine()
    
    # Transition to DAMP
    sm.update_state(FSMState.DAMP, fsm_mode=0)
    assert sm._current_state.fsm_state == FSMState.DAMP
    
    # Get allowed transitions for DAMP
    allowed = sm.get_allowed_transitions()
    print(f"\nDAMP allows: {[s.name for s in allowed]}")
    
    # DAMP should allow MANY transitions (emergency access to all modes)
    assert FSMState.ZERO_TORQUE in allowed
    assert FSMState.DAMP in allowed
    assert FSMState.START in allowed, "DAMP should allow START"
    assert FSMState.SQUAT in allowed, "DAMP should allow SQUAT"
    assert FSMState.STAND_UP in allowed, "DAMP should allow STAND_UP"
    assert FSMState.SIT in allowed, "DAMP should allow SIT"
    print("✓ DAMP transitions correct (START, SQUAT accessible)")


def test_state_machine_start():
    """Test START state transitions"""
    sm = StateMachine()
    
    # Transition to START
    sm.update_state(FSMState.START, fsm_mode=0)
    assert sm._current_state.fsm_state == FSMState.START
    
    # Get allowed transitions for START
    allowed = sm.get_allowed_transitions()
    print(f"\nSTART allows: {[s.name for s in allowed]}")
    
    # START should allow LOCK_STAND and others
    assert FSMState.DAMP in allowed
    assert FSMState.SIT in allowed
    assert FSMState.SQUAT in allowed
    assert FSMState.LOCK_STAND in allowed
    assert FSMState.RUN in allowed
    print("✓ START transitions correct")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing State Machine Transitions")
    print("=" * 60)
    
    test_state_machine_zero_torque()
    test_state_machine_damp()
    test_state_machine_start()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
