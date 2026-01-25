#!/usr/bin/env python3
"""
Complete integration test for FSM state tracking
Tests subscription, state updates, and UI synchronization
"""

import asyncio
import sys

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

# Import our app modules
sys.path.insert(0, '/root/G1/unitree_sdk2')
from g1_app.api.constants import FSMState, Topic
from g1_app.core.state_machine import StateMachine

ROBOT_IP = "192.168.86.2"
ROBOT_SN = "E21D1000PAHBMB06"

async def test_state_tracking():
    """Test complete state tracking system"""
    
    print("=" * 80)
    print("G1 FSM STATE TRACKING - INTEGRATION TEST")
    print("=" * 80)
    print()
    
    # Initialize state machine
    print("1. Initializing state machine...")
    state_machine = StateMachine()
    print(f"   Initial state: {state_machine.fsm_state.name} ({state_machine.fsm_state.value})")
    print()
    
    # Connect to robot
    print(f"2. Connecting to robot {ROBOT_IP}...")
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    await conn.connect()
    print("   ✅ Connected")
    print()
    
    # Track state updates
    update_count = 0
    last_fsm_id = None
    
    def on_state_update(data: dict):
        nonlocal update_count, last_fsm_id
        
        if data.get('type') == 'msg':
            state_data = data.get('data', {})
            fsm_id = state_data.get('fsm_id')
            fsm_mode = state_data.get('fsm_mode')
            task_id = state_data.get('task_id')
            
            # Only log when state changes
            if fsm_id != last_fsm_id:
                update_count += 1
                last_fsm_id = fsm_id
                
                # Try to map to FSM state
                try:
                    fsm_state = FSMState(fsm_id)
                    state_name = fsm_state.name
                    print(f"   📥 Update #{update_count}: FSM State = {state_name} ({fsm_id}), Mode = {fsm_mode}, Task = {task_id}")
                    
                    # Update state machine
                    state_machine.update_state(fsm_state, fsm_mode=fsm_mode, task_id=task_id)
                    
                except ValueError:
                    print(f"   ⚠️  Update #{update_count}: Unknown FSM ID {fsm_id} (mode={fsm_mode})")
    
    # Subscribe to state updates
    print(f"3. Subscribing to {Topic.SPORT_MODE_STATE_LF}...")
    conn.datachannel.pub_sub.subscribe(Topic.SPORT_MODE_STATE_LF, on_state_update)
    print("   ✅ Subscribed")
    print()
    
    # Listen for updates
    print("4. Listening for state updates (10 seconds)...")
    print("   (Try moving robot with Android app or remote control)")
    print()
    
    await asyncio.sleep(10)
    
    # Results
    print()
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print()
    
    if last_fsm_id is not None:
        try:
            fsm_state = FSMState(last_fsm_id)
            print(f"✅ SUCCESS! State tracking is working!")
            print()
            print(f"Current Robot State:")
            print(f"  FSM State:  {fsm_state.name} ({fsm_state.value})")
            print(f"  FSM Mode:   {state_machine.current_state.fsm_mode}")
            print(f"  Task ID:    {state_machine.current_state.task_id}")
            print(f"  Updates:    {update_count} state changes detected")
            print()
            
            # Test state machine transitions
            print(f"Valid transitions from {fsm_state.name}:")
            transitions = StateMachine.TRANSITIONS.get(fsm_state, set())
            for target in sorted(transitions, key=lambda s: s.value):
                print(f"  → {target.name} ({target.value})")
            
            if not transitions:
                print(f"  (No transitions defined from this state)")
            
        except ValueError:
            print(f"❌ Robot is in unknown state {last_fsm_id}")
            print(f"   This state is not in our FSM enum!")
            print()
            print(f"Known states:")
            for state in FSMState:
                print(f"  {state.name} = {state.value}")
    else:
        print(f"❌ FAILED! No state updates received")
        print(f"   Check:")
        print(f"   1. Robot is powered on")
        print(f"   2. Network connection is working (can ping {ROBOT_IP})")
        print(f"   3. WebRTC connection succeeded")
    
    print()
    print("Disconnecting...")
    await conn.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test_state_tracking())
