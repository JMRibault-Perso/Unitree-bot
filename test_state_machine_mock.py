#!/usr/bin/env python3
"""
Mock State Machine Test - Verify transitions work correctly
"""

import sys
sys.path.insert(0, '/root/G1/unitree_sdk2')

# Import without triggering robot controller
from g1_app.api.constants import FSMState

# Manually define the transitions to test (copy from state_machine.py)
TRANSITIONS = {
    FSMState.ZERO_TORQUE: {
        FSMState.DAMP,
    },
    
    FSMState.DAMP: {
        FSMState.ZERO_TORQUE,
        FSMState.START,
        FSMState.SIT,
        FSMState.SQUAT,
        FSMState.SQUAT_TO_STAND,
        FSMState.LYING_STAND,
    },
    
    FSMState.START: {
        FSMState.DAMP,
        FSMState.SIT,
        FSMState.STAND_TO_SQUAT,
        FSMState.LOCK_STAND,
        FSMState.LOCK_STAND_ADV,
        FSMState.RUN,
        FSMState.SQUAT_TO_STAND,
        FSMState.LYING_STAND,
    },
    
    FSMState.LOCK_STAND: {
        FSMState.DAMP,
        FSMState.START,
        FSMState.SIT,
        FSMState.STAND_TO_SQUAT,
        FSMState.LOCK_STAND_ADV,
        FSMState.RUN,
        FSMState.SQUAT_TO_STAND,
        FSMState.LYING_STAND,
    },
    
    FSMState.LOCK_STAND_ADV: {
        FSMState.DAMP,
        FSMState.START,
        FSMState.SIT,
        FSMState.STAND_TO_SQUAT,
        FSMState.LOCK_STAND,
        FSMState.RUN,
        FSMState.SQUAT_TO_STAND,
        FSMState.LYING_STAND,
    },
    
    FSMState.RUN: {
        FSMState.DAMP,
        FSMState.START,
        FSMState.SIT,
        FSMState.STAND_TO_SQUAT,
        FSMState.LOCK_STAND,
        FSMState.LOCK_STAND_ADV,
        FSMState.SQUAT_TO_STAND,
        FSMState.LYING_STAND,
    },
    
    FSMState.SQUAT_TO_STAND: {
        FSMState.DAMP,
        FSMState.LOCK_STAND,
        FSMState.LOCK_STAND_ADV,
        FSMState.RUN,
        FSMState.SQUAT_TO_STAND,
        FSMState.LYING_STAND,
    },
    
    FSMState.LYING_STAND: {
        FSMState.DAMP,
        FSMState.LOCK_STAND,
        FSMState.LOCK_STAND_ADV,
        FSMState.RUN,
        FSMState.SQUAT_TO_STAND,
        FSMState.LYING_STAND,
    },
    
    FSMState.SIT: {
        FSMState.START,
        FSMState.STAND_UP,
    },
    
    FSMState.SQUAT: {
        FSMState.START,
        FSMState.SQUAT_TO_STAND,
    },
    
    FSMState.STAND_UP: {
        FSMState.START,
        FSMState.LOCK_STAND,
        FSMState.LOCK_STAND_ADV,
        FSMState.RUN,
    },
    
    FSMState.STAND_TO_SQUAT: {
        FSMState.SQUAT,
        FSMState.START,
    },
}


def can_transition(from_state: FSMState, to_state: FSMState) -> bool:
    """Check if transition is valid"""
    # Always allow transition to same state
    if from_state == to_state:
        return True
    
    # Always allow transition to DAMP or ZERO_TORQUE (emergency stop)
    if to_state in [FSMState.DAMP, FSMState.ZERO_TORQUE]:
        return True
    
    # Check transition table
    valid_targets = TRANSITIONS.get(from_state, set())
    return to_state in valid_targets


def test_state_transitions(from_state: FSMState):
    """Test all transitions from a given state"""
    print(f"\n{'='*80}")
    print(f"Testing transitions FROM: {from_state.name} ({from_state.value})")
    print(f"{'='*80}\n")
    
    # Get expected allowed transitions
    expected_transitions = TRANSITIONS.get(from_state, set())
    print(f"Expected transitions: {len(expected_transitions)}")
    for state in sorted(expected_transitions, key=lambda x: x.value):
        print(f"  ✓ {state.name:20s} ({state.value})")
    
    print(f"\n{'─'*80}")
    print("Testing ALL possible states:")
    print(f"{'─'*80}\n")
    
    all_states = [
        FSMState.ZERO_TORQUE,
        FSMState.DAMP,
        FSMState.SQUAT,
        FSMState.SIT,
        FSMState.STAND_UP,
        FSMState.START,
        FSMState.LOCK_STAND,
        FSMState.LOCK_STAND_ADV,
        FSMState.SQUAT_TO_STAND,
        FSMState.STAND_TO_SQUAT,
        FSMState.LYING_STAND,
        FSMState.RUN,
    ]
    
    allowed_count = 0
    blocked_count = 0
    
    for to_state in all_states:
        is_allowed = can_transition(from_state, to_state)
        is_current = (from_state == to_state)
        
        if is_current:
            symbol = "→"
            status = "CURRENT"
            color = ""
        elif is_allowed:
            symbol = "✓"
            status = "ALLOWED"
            color = "\033[92m"  # Green
            allowed_count += 1
        else:
            symbol = "✗"
            status = "BLOCKED"
            color = "\033[91m"  # Red
            blocked_count += 1
        
        reset = "\033[0m" if color else ""
        print(f"{color}{symbol} {to_state.name:20s} ({to_state.value:3d}) - {status}{reset}")
    
    print(f"\n{'─'*80}")
    print(f"Summary: {allowed_count} allowed, {blocked_count} blocked")
    print(f"{'─'*80}\n")


def test_balanced_control_interconnectivity():
    """Test that all balanced control states can transition to each other"""
    print(f"\n{'='*80}")
    print("Testing BALANCED CONTROL states interconnectivity")
    print(f"{'='*80}\n")
    
    balanced_states = [
        FSMState.LOCK_STAND,      # 500
        FSMState.LOCK_STAND_ADV,  # 501
        FSMState.SQUAT_TO_STAND,  # 706
        FSMState.LYING_STAND,     # 708
        FSMState.RUN,             # 801
    ]
    
    print("All balanced control states should be able to transition to each other:\n")
    
    errors = []
    
    for from_state in balanced_states:
        for to_state in balanced_states:
            if from_state == to_state:
                continue
            
            is_allowed = can_transition(from_state, to_state)
            symbol = "✓" if is_allowed else "✗"
            color = "\033[92m" if is_allowed else "\033[91m"
            reset = "\033[0m"
            
            print(f"{color}{symbol}{reset} {from_state.name:20s} → {to_state.name:20s}")
            
            if not is_allowed:
                errors.append(f"{from_state.name} → {to_state.name}")
    
    if errors:
        print(f"\n\033[91m❌ FAILED: {len(errors)} transitions not allowed:\033[0m")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n\033[92m✓ SUCCESS: All balanced control states are interconnected!\033[0m")
    
    return len(errors) == 0


def main():
    print("\n" + "="*80)
    print("STATE MACHINE MOCK TEST")
    print("="*80)
    
    # Test from RUN state (current robot state)
    test_state_transitions(FSMState.RUN)
    
    # Test from LOCK_STAND
    test_state_transitions(FSMState.LOCK_STAND)
    
    # Test interconnectivity of balanced states
    success = test_balanced_control_interconnectivity()
    
    if success:
        print("\n\033[92m✅ All tests passed!\033[0m\n")
        return 0
    else:
        print("\n\033[91m❌ Some tests failed!\033[0m\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
