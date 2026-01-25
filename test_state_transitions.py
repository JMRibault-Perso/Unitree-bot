#!/usr/bin/env python3
"""
Unit tests for FSM state transitions - ensures UI and backend match perfectly
"""

import unittest
from g1_app.api.constants import FSMState
from g1_app.core.state_machine import StateMachine


class TestStateTransitions(unittest.TestCase):
    """Test all FSM state transitions match expected behavior"""

    def setUp(self):
        self.sm = StateMachine()

    def test_damp_state_transitions(self):
        """Test transitions from DAMP mode - most critical for UI"""
        # Set state to DAMP 
        self.sm.update_state(FSMState.DAMP)
        
        # Get allowed transitions
        allowed = self.sm.get_allowed_transitions()
        allowed_names = {s.name for s in allowed}
        
        print(f"\n🔍 DAMP state transitions:")
        print(f"Expected: ZERO_TORQUE, START, SIT, SQUAT, SQUAT_TO_STAND, STAND_UP, DAMP")
        print(f"Actual: {sorted(allowed_names)}")
        
        # Should allow these transitions from DAMP
        expected_from_damp = {
            'ZERO_TORQUE',    # Back to zero torque
            'START',          # Enter ready mode  
            'SIT',            # Sit down
            'SQUAT',          # Squat position
            'SQUAT_TO_STAND', # Emergency recovery (squat up/down)
            'STAND_UP',       # Emergency recovery (stand from lying) 
            'DAMP'            # Self (added by emergency logic)
        }
        
        # Verify all expected transitions are present
        for expected in expected_from_damp:
            self.assertIn(expected, allowed_names, 
                f"Missing transition from DAMP: {expected}")
        
        # Should be exactly these transitions
        self.assertEqual(allowed_names, expected_from_damp,
            f"DAMP transitions mismatch.\nExpected: {expected_from_damp}\nActual: {allowed_names}")

    def test_run_state_transitions(self):
        """Test transitions from RUN mode"""
        self.sm.update_state(FSMState.RUN)
        allowed = self.sm.get_allowed_transitions()
        allowed_names = {s.name for s in allowed}
        
        print(f"\n🔍 RUN state transitions:")
        print(f"Actual: {sorted(allowed_names)}")
        
        expected_from_run = {
            'DAMP',           # Emergency stop
            'LOCK_STAND',     # Slow down to walk mode
            'SIT',            # Sit down
            'SQUAT_TO_STAND', # Squat toggle
            'ZERO_TORQUE'     # Emergency stop (added by logic)
        }
        
        self.assertEqual(allowed_names, expected_from_run,
            f"RUN transitions mismatch.\nExpected: {expected_from_run}\nActual: {allowed_names}")

    def test_walk_state_transitions(self):
        """Test transitions from LOCK_STAND (Walk) mode"""
        self.sm.update_state(FSMState.LOCK_STAND)
        allowed = self.sm.get_allowed_transitions()
        allowed_names = {s.name for s in allowed}
        
        print(f"\n🔍 LOCK_STAND (Walk) state transitions:")
        print(f"Actual: {sorted(allowed_names)}")
        
        expected_from_walk = {
            'DAMP',           # Emergency stop
            'RUN',            # Speed up to run mode
            'SIT',            # Sit down
            'SQUAT_TO_STAND', # Squat toggle
            'ZERO_TORQUE'     # Emergency stop (added by logic)
        }
        
        self.assertEqual(allowed_names, expected_from_walk,
            f"LOCK_STAND transitions mismatch.\nExpected: {expected_from_walk}\nActual: {allowed_names}")

    def test_ui_backend_state_mapping(self):
        """Test that UI FSM_STATES names match backend FSMState enum names"""
        
        # These are the states that should be in the UI
        ui_states = [
            {'name': 'ZERO_TORQUE', 'value': 0},
            {'name': 'DAMP', 'value': 1},
            {'name': 'SQUAT', 'value': 2},
            {'name': 'SIT', 'value': 3},
            {'name': 'LOCK_STANDING', 'value': 4},
            {'name': 'START', 'value': 200},
            {'name': 'LOCK_STAND', 'value': 500},
            {'name': 'STAND_UP', 'value': 702},
            {'name': 'SQUAT_TO_STAND', 'value': 706},
            {'name': 'RUN', 'value': 801}
        ]
        
        # Verify each UI state has a corresponding backend enum
        for ui_state in ui_states:
            state_name = ui_state['name']
            state_value = ui_state['value']
            
            # Check if enum exists
            try:
                backend_state = FSMState[state_name]
                self.assertEqual(backend_state.value, state_value,
                    f"Value mismatch for {state_name}: UI={state_value}, Backend={backend_state.value}")
                print(f"✓ {state_name} ({state_value}) - MATCH")
            except KeyError:
                self.fail(f"UI state '{state_name}' not found in backend FSMState enum")

    def test_emergency_transitions_always_available(self):
        """Test that DAMP and ZERO_TORQUE are always available (except from themselves)"""
        
        all_states = [
            FSMState.ZERO_TORQUE, FSMState.DAMP, FSMState.SQUAT, FSMState.SIT,
            FSMState.LOCK_STANDING, FSMState.START, FSMState.LOCK_STAND,
            FSMState.STAND_UP, FSMState.SQUAT_TO_STAND, FSMState.RUN
        ]
        
        for current_state in all_states:
            self.sm.update_state(current_state)
            allowed = self.sm.get_allowed_transitions()
            allowed_names = {s.name for s in allowed}
            
            # DAMP should always be available
            self.assertIn('DAMP', allowed_names,
                f"DAMP not available from {current_state.name}")
            
            # ZERO_TORQUE should always be available  
            self.assertIn('ZERO_TORQUE', allowed_names,
                f"ZERO_TORQUE not available from {current_state.name}")


def run_state_transition_test():
    """Run the test suite and return results"""
    
    print("🧪 RUNNING FSM STATE TRANSITION TESTS")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStateTransitions)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=open('/tmp/test_output.txt', 'w'))
    result = runner.run(suite)
    
    # Print results to console
    with open('/tmp/test_output.txt', 'r') as f:
        output = f.read()
        print(output)
    
    return result.wasSuccessful(), result.failures, result.errors


if __name__ == '__main__':
    success, failures, errors = run_state_transition_test()
    
    if success:
        print("\n✅ ALL TESTS PASSED - State transitions are correct")
    else:
        print(f"\n❌ TESTS FAILED - {len(failures)} failures, {len(errors)} errors")
        for failure in failures:
            print(f"\nFAILURE: {failure[0]}")
            print(failure[1])
        for error in errors:
            print(f"\nERROR: {error[0]}")
            print(error[1])
    
    exit(0 if success else 1)