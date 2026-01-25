#!/usr/bin/env python3
"""
Comprehensive fix for ALL UI state transition issues
"""

import sys
import os
sys.path.append('/root/G1/unitree_sdk2')

from g1_app.api.constants import FSMState
from g1_app.core.state_machine import StateMachine

def test_all_state_transitions():
    """Test all state transitions and identify issues"""
    
    print("🧪 TESTING ALL FSM STATE TRANSITIONS")
    print("=" * 60)
    
    sm = StateMachine()
    
    # Test all possible states
    test_states = [
        (FSMState.ZERO_TORQUE, "ZERO_TORQUE"),
        (FSMState.DAMP, "DAMP"),
        (FSMState.SQUAT, "SQUAT"),
        (FSMState.SIT, "SIT"),
        (FSMState.LOCK_STANDING, "LOCK_STANDING"),
        (FSMState.START, "START"),
        (FSMState.LOCK_STAND, "LOCK_STAND"),
        (FSMState.STAND_UP, "STAND_UP"),
        (FSMState.SQUAT_TO_STAND, "SQUAT_TO_STAND"),
        (FSMState.RUN, "RUN")
    ]
    
    all_results = {}
    
    for state_enum, state_name in test_states:
        sm.update_state(state_enum)
        allowed = sm.get_allowed_transitions()
        allowed_names = [s.name for s in sorted(allowed, key=lambda x: x.value)]
        
        print(f"\n📍 FROM {state_name} ({state_enum.value}):")
        print(f"   Allowed transitions: {allowed_names}")
        print(f"   Count: {len(allowed_names)}")
        
        all_results[state_name] = allowed_names
    
    print("\n" + "=" * 60)
    print("🎯 EXPECTED vs ACTUAL ANALYSIS")
    print("=" * 60)
    
    # Expected transitions based on documentation
    expected = {
        'ZERO_TORQUE': ['DAMP', 'ZERO_TORQUE'],
        'DAMP': ['DAMP', 'SQUAT', 'SQUAT_TO_STAND', 'SIT', 'STAND_UP', 'START', 'ZERO_TORQUE'],
        'RUN': ['DAMP', 'LOCK_STAND', 'SIT', 'SQUAT_TO_STAND', 'ZERO_TORQUE'],
        'LOCK_STAND': ['DAMP', 'RUN', 'SIT', 'SQUAT_TO_STAND', 'ZERO_TORQUE'],
    }
    
    for state, expected_trans in expected.items():
        actual = sorted(all_results.get(state, []))
        expected_sorted = sorted(expected_trans)
        
        print(f"\n{state}:")
        print(f"  Expected: {expected_sorted}")
        print(f"  Actual:   {actual}")
        
        if actual == expected_sorted:
            print(f"  ✅ MATCH")
        else:
            missing = set(expected_sorted) - set(actual)
            extra = set(actual) - set(expected_sorted)
            print(f"  ❌ MISMATCH")
            if missing:
                print(f"     Missing: {missing}")
            if extra:
                print(f"     Extra: {extra}")
    
    print("\n" + "=" * 60)
    print("🔧 UI FSM_STATES VALIDATION")
    print("=" * 60)
    
    # UI states that should exist
    ui_states = [
        ('ZERO_TORQUE', 0),
        ('DAMP', 1),
        ('SQUAT', 2),
        ('SIT', 3),
        ('LOCK_STANDING', 4),
        ('START', 200),
        ('LOCK_STAND', 500),
        ('STAND_UP', 702),
        ('SQUAT_TO_STAND', 706),
        ('RUN', 801)
    ]
    
    for name, value in ui_states:
        try:
            backend_state = FSMState[name]
            if backend_state.value == value:
                print(f"✅ {name:<15} ({value:>3}) - PERFECT MATCH")
            else:
                print(f"❌ {name:<15} ({value:>3}) - VALUE MISMATCH: backend={backend_state.value}")
        except KeyError:
            print(f"❌ {name:<15} ({value:>3}) - NOT FOUND IN BACKEND")
    
    return all_results


def create_ui_fix():
    """Generate JavaScript code to fix UI state transitions"""
    
    print("\n" + "=" * 60)
    print("🔧 GENERATING UI FIXES")
    print("=" * 60)
    
    # Generate corrected FSM_STATES array for UI
    ui_fix = """
// CORRECTED FSM_STATES array - matches backend exactly
const FSM_STATES = [
    { name: 'ZERO_TORQUE', value: 0, description: 'Motors Off' },
    { name: 'DAMP', value: 1, description: 'Safe Mode (Orange)' },
    { name: 'SQUAT', value: 2, description: 'Squat Position' },
    { name: 'SIT', value: 3, description: 'Sitting (Green)' },
    { name: 'LOCK_STANDING', value: 4, description: 'Standing Up' },
    { name: 'START', value: 200, description: 'Ready/Standing (Blue)' },
    { name: 'LOCK_STAND', value: 500, description: 'Walk Mode' },
    { name: 'STAND_UP', value: 702, description: 'Stand Up (from lying down)' },
    { name: 'SQUAT_TO_STAND', value: 706, description: 'Squat Down/Up (context-sensitive)' },
    { name: 'RUN', value: 801, description: 'Run Mode (Faster)' }
];

// CORRECTED updateStateButtons function
function updateStateButtons() {
    if (!isConnected) {
        console.log('updateStateButtons: Not connected, skipping...');
        return;
    }
    
    const grid = document.getElementById('stateGrid');
    if (!grid) {
        console.error('updateStateButtons: stateGrid not found');
        return;
    }
    
    grid.innerHTML = '';
    
    console.log('🎯 updateStateButtons - State Check:');
    console.log('  currentFsmState:', currentFsmState);
    console.log('  allowedTransitions:', allowedTransitions);
    console.log('  allowedTransitions type:', typeof allowedTransitions);
    console.log('  allowedTransitions length:', allowedTransitions ? allowedTransitions.length : 'undefined');
    
    // Ensure allowedTransitions is an array
    const transitions = Array.isArray(allowedTransitions) ? allowedTransitions : [];
    
    FSM_STATES.forEach((state, index) => {
        const button = document.createElement('button');
        button.className = 'state-button';
        
        // Check if this is the current state  
        const isCurrent = state.name === currentFsmState;
        if (isCurrent) {
            button.classList.add('current');
        }
        
        // Check if transition is allowed - CRITICAL FIX
        const isAllowed = transitions.includes(state.name);
        
        console.log(`  State ${index}: ${state.name} (${state.value})`);
        console.log(`    Current: ${isCurrent}, Allowed: ${isAllowed}`);
        
        if (!isAllowed && !isCurrent) {
            button.classList.add('invalid');
            button.disabled = true;
            console.log(`    ❌ DISABLED`);
        } else {
            console.log(`    ✅ ENABLED`);
        }
        
        // User-friendly display names
        let displayName = state.name;
        switch(state.name) {
            case 'LOCK_STAND':
                displayName = 'WALK';
                break;
            case 'LOCK_STANDING':
                displayName = 'STAND UP';
                break;
            case 'SQUAT_TO_STAND':
                const currentStateObj = FSM_STATES.find(s => s.name === currentFsmState);
                const currentStateValue = currentStateObj ? currentStateObj.value : null;
                displayName = (currentStateValue === 0 || currentStateValue === 1) ? 'SQUAT UP' : 'SQUAT DOWN';
                break;
            case 'STAND_UP':
                displayName = 'STAND UP';
                break;
        }
        
        button.innerHTML = `
            <div class="state-name">${displayName.replace(/_/g, ' ')}</div>
            <div class="state-id">ID: ${state.value}</div>
        `;
        
        if (!button.disabled) {
            button.onclick = () => setState(state.name);
        }
        
        grid.appendChild(button);
    });
    
    console.log('✅ updateStateButtons completed');
}
"""
    
    print("Generated UI Fix JavaScript (copy to index.html):")
    print(ui_fix)
    
    return ui_fix


if __name__ == '__main__':
    test_results = test_all_state_transitions()
    ui_fix = create_ui_fix()
    
    print(f"\n🎯 SUMMARY: Tested {len(test_results)} states")
    print("Copy the generated JavaScript code to fix UI state transitions!")