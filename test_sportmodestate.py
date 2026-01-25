#!/usr/bin/env python3
"""
Test script to verify rt/sportmodestate subscription works
"""

import asyncio
import sys
import json

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

ROBOT_IP = "192.168.86.2"
ROBOT_SN = "E21D1000PAHBMB06"

async def test_sportmodestate():
    """Test subscribing to rt/sportmodestate topic"""
    
    print("=" * 70)
    print("Testing rt/sportmodestate subscription")
    print("=" * 70)
    print(f"Robot: {ROBOT_IP} / {ROBOT_SN}")
    print()
    
    print("Connecting to robot...")
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    await conn.connect()
    print("✅ Connected\n")
    
    state_updates = []
    
    def on_state_update(data: dict):
        state_updates.append(data)
        print(f"📥 Received state update:")
        print(f"   Type: {type(data)}")
        print(f"   Data: {json.dumps(data, indent=2) if isinstance(data, dict) else data}\n")
        
        # Try to access fields
        if isinstance(data, dict) and 'data' in data:
            state_data = data['data']
            print(f"   State data keys: {state_data.keys() if isinstance(state_data, dict) else 'N/A'}")
            
            if isinstance(state_data, dict):
                fsm_id = state_data.get('fsm_id')
                fsm_mode = state_data.get('fsm_mode')
                task_id = state_data.get('task_id')
                
                print(f"   fsm_id: {fsm_id}")
                print(f"   fsm_mode: {fsm_mode}")
                print(f"   task_id: {task_id}")
                
                # Map FSM ID to state name
                fsm_map = {
                    0: "ZERO_TORQUE",
                    1: "DAMP",
                    2: "SQUAT",
                    3: "SIT",
                    4: "STAND_UP",
                    200: "START (Ready/Standing)",
                    500: "LOCK_STAND (Walk/Run Mode)",
                    706: "SQUAT_TO_STAND",
                    707: "STAND_TO_SQUAT",
                    708: "LYING_STAND"
                }
                
                if fsm_id is not None:
                    state_name = fsm_map.get(fsm_id, f"Unknown FSM {fsm_id}")
                    print(f"   → Current FSM State: {state_name}")
                print()
    
    # Subscribe to sportmodestate
    print("Subscribing to rt/sportmodestate...")
    conn.datachannel.pub_sub.subscribe("rt/sportmodestate", on_state_update)
    
    # Also try low-freq topic
    print("Also subscribing to rt/lf/sportmodestate...")
    conn.datachannel.pub_sub.subscribe("rt/lf/sportmodestate", on_state_update)
    
    print("\n⏳ Listening for 10 seconds...\n")
    await asyncio.sleep(10)
    
    print("=" * 70)
    print(f"RESULT: Received {len(state_updates)} state updates")
    print("=" * 70)
    
    if state_updates:
        print("\n✅ SUCCESS! The rt/sportmodestate topic is working!")
        print("\nFirst update sample:")
        print(json.dumps(state_updates[0], indent=2))
    else:
        print("\n❌ FAILED! No state updates received from rt/sportmodestate")
        print("   The topic may not be broadcasting, or data format is different")
    
    print("\nDisconnecting...")
    await conn.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test_sportmodestate())
