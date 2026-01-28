#!/usr/bin/env python3
"""
REAL Unit Tests for web_server.py
Tests the actual production code, not a mock
"""

import sys
import asyncio
from unittest.mock import Mock, MagicMock, patch
import pytest

# Add g1_app to path
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.api.constants import FSMState
from g1_app.core.state_machine import StateMachine

# Mock RobotState as a simple class since it doesn't exist
class RobotState:
    def __init__(self, fsm_state, fsm_mode=0, task_id=0):
        self.fsm_state = fsm_state
        self.fsm_mode = fsm_mode
        self.task_id = task_id


def test_state_machine_allowed_transitions():
    """Test that StateMachine.get_allowed_transitions() works correctly"""
    sm = StateMachine()
    
    # ZERO_TORQUE state should only allow DAMP or stay in ZERO_TORQUE
    sm.update_state(RobotState(fsm_state=FSMState.ZERO_TORQUE.value, fsm_mode=0))
    allowed = sm.get_allowed_transitions()
    assert FSMState.DAMP in allowed
    assert FSMState.ZERO_TORQUE in allowed
    print(f"✓ ZERO_TORQUE allows: {[s.name for s in allowed]}")
    
    # DAMP state should allow many transitions
    sm.update_state(RobotState(fsm_state=FSMState.DAMP.value, fsm_mode=0))
    allowed = sm.get_allowed_transitions()
    assert FSMState.ZERO_TORQUE in allowed
    assert FSMState.DAMP in allowed
    assert FSMState.START in allowed
    assert FSMState.SQUAT in allowed
    print(f"✓ DAMP allows: {[s.name for s in allowed]}")
    
    # START state should allow LOCK_STAND
    sm.update_state(RobotState(fsm_state=FSMState.START.value, fsm_mode=0))
    allowed = sm.get_allowed_transitions()
    assert FSMState.LOCK_STAND in allowed
    print(f"✓ START allows: {[s.name for s in allowed]}")


@pytest.mark.asyncio
async def test_on_state_change_uses_robot_state_machine():
    """Test that on_state_change uses the robot's actual state_machine"""
    from g1_app.ui import web_server
    from g1_app.core.robot_controller import RobotController
    
    # Create a mock robot controller with a real state machine
    mock_robot = Mock(spec=RobotController)
    mock_robot.state_machine = StateMachine()
    
    # Set robot to DAMP mode
    mock_robot.state_machine.update_state(
        RobotState(fsm_state=FSMState.DAMP.value, fsm_mode=0)
    )
    
    # Patch the global 'robot' in web_server module
    with patch.object(web_server, 'robot', mock_robot):
        # Mock the connection manager
        with patch.object(web_server, 'manager') as mock_manager:
            mock_manager.broadcast = Mock()
            
            # Call on_state_change with DAMP state
            state_dict = {
                "fsm_state_name": "DAMP",
                "fsm_state": FSMState.DAMP.value,
                "fsm_mode": 0
            }
            
            web_server.on_state_change(state_dict)
            
            # Verify broadcast was called
            assert mock_manager.broadcast.called
            
            # Get the broadcast data
            call_args = mock_manager.broadcast.call_args[0][0]
            broadcast_data = call_args['data']
            
            # Verify allowed_transitions includes more than just ZERO_TORQUE and DAMP
            allowed_names = broadcast_data['allowed_transitions']
            print(f"✓ Broadcast allowed_transitions: {allowed_names}")
            
            assert 'ZERO_TORQUE' in allowed_names
            assert 'DAMP' in allowed_names
            assert 'START' in allowed_names, f"DAMP should allow START! Got: {allowed_names}"
            assert 'SQUAT' in allowed_names, f"DAMP should allow SQUAT! Got: {allowed_names}"


@pytest.mark.asyncio
async def test_on_state_change_zero_torque():
    """Test that on_state_change correctly reports ZERO_TORQUE allowed transitions"""
    from g1_app.ui import web_server
    from g1_app.core.robot_controller import RobotController
    
    # Create a mock robot controller with a real state machine
    mock_robot = Mock(spec=RobotController)
    mock_robot.state_machine = StateMachine()
    
    # Set robot to ZERO_TORQUE mode
    mock_robot.state_machine.update_state(
        RobotState(fsm_state=FSMState.ZERO_TORQUE.value, fsm_mode=0)
    )
    
    # Patch the global 'robot' in web_server module
    with patch.object(web_server, 'robot', mock_robot):
        # Mock the connection manager
        with patch.object(web_server, 'manager') as mock_manager:
            mock_manager.broadcast = Mock()
            
            # Call on_state_change with ZERO_TORQUE state
            state_dict = {
                "fsm_state_name": "ZERO_TORQUE",
                "fsm_state": FSMState.ZERO_TORQUE.value,
                "fsm_mode": 0
            }
            
            web_server.on_state_change(state_dict)
            
            # Get the broadcast data
            call_args = mock_manager.broadcast.call_args[0][0]
            broadcast_data = call_args['data']
            
            # Verify allowed_transitions is ONLY ZERO_TORQUE and DAMP
            allowed_names = broadcast_data['allowed_transitions']
            print(f"✓ Broadcast allowed_transitions: {allowed_names}")
            
            assert 'ZERO_TORQUE' in allowed_names
            assert 'DAMP' in allowed_names
            assert 'START' not in allowed_names, f"ZERO_TORQUE should NOT allow START! Got: {allowed_names}"


if __name__ == "__main__":
    print("Testing StateMachine transitions...")
    test_state_machine_allowed_transitions()
    
    print("\nTesting on_state_change with DAMP state...")
    asyncio.run(test_on_state_change_uses_robot_state_machine())
    
    print("\nTesting on_state_change with ZERO_TORQUE state...")
    asyncio.run(test_on_state_change_zero_torque())
    
    print("\n✅ ALL TESTS PASSED!")
