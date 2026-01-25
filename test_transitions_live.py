#!/usr/bin/env python3
"""
Test allowed transitions with actual robot connection
"""
import asyncio
import sys
import logging

sys.path.insert(0, '/root/G1/unitree_sdk2')

# Disable debug logging
logging.getLogger('g1_app.core.robot_controller').setLevel(logging.WARNING)

from g1_app import RobotController
from g1_app.api.constants import FSMState

async def test_transitions():
    """Test what transitions are actually being returned"""
    
    # Connect to robot
    print("Connecting to robot...")
    robot = RobotController("192.168.86.2", "E21D1000PAHBMB06")
    await robot.connect()
    
    # Wait for state to stabilize
    await asyncio.sleep(2)
    
    # Get current state
    current = robot.state_machine.fsm_state
    print(f"\n{'='*80}")
    print(f"Current FSM State: {current.name} ({current.value})")
    print(f"{'='*80}\n")
    
    # Get transitions from dict directly
    transitions_dict = robot.state_machine.TRANSITIONS.get(current, set())
    print(f"Transitions from TRANSITIONS dict ({len(transitions_dict)}):")
    for state in sorted(transitions_dict, key=lambda x: x.value):
        print(f"  - {state.name:20s} ({state.value})")
    
    # Get transitions from method
    allowed = robot.state_machine.get_allowed_transitions()
    print(f"\nTransitions from get_allowed_transitions() ({len(allowed)}):")
    for state in sorted(allowed, key=lambda x: x.value):
        print(f"  - {state.name:20s} ({state.value})")
    
    # Verify key transitions exist
    print(f"\n{'─'*80}")
    print("Verifying key transitions:")
    print(f"{'─'*80}")
    
    expected = [
        FSMState.LOCK_STAND,
        FSMState.LOCK_STAND_ADV,
        FSMState.STAND_TO_SQUAT,
        FSMState.DAMP,
    ]
    
    for state in expected:
        exists = state in allowed
        symbol = "✓" if exists else "✗"
        print(f"{symbol} {state.name:20s} - {'FOUND' if exists else 'MISSING'}")
    
    # Disconnect
    await robot.disconnect()
    
    # Return success if all expected transitions found
    return all(state in allowed for state in expected)

if __name__ == "__main__":
    result = asyncio.run(test_transitions())
    sys.exit(0 if result else 1)
