#!/usr/bin/env python3
"""
Test WebSocket broadcasts to verify UI updates
"""
import asyncio
import json
import websockets
import requests

async def test_ui_updates():
    """Connect to WebSocket and monitor state updates"""
    print("=" * 60)
    print("Testing UI Updates via WebSocket")
    print("=" * 60)
    
    # Connect to robot first
    print("\n1. Connecting to robot...")
    response = requests.post(
        "http://localhost:8000/api/connect?ip=192.168.86.16&serial_number=E21D1000PAHBMB06"
    )
    print(f"   Connected: {response.status_code}")
    
    # Connect to WebSocket
    print("\n2. Connecting to WebSocket...")
    async with websockets.connect("ws://localhost:8000/ws") as websocket:
        print("   WebSocket connected")
        
        # Listen for initial state
        print("\n3. Waiting for initial state broadcast...")
        message = await websocket.recv()
        data = json.loads(message)
        print(f"   Initial state: {data['type']}")
        if data['type'] == 'state_changed':
            print(f"   fsm_state: {data['fsm_state']}")
            print(f"   allowed_transitions: {data.get('allowed_transitions', 'MISSING!')}")
        
        # Change to DAMP mode (fsm_id=1)
        print("\n4. Changing to DAMP mode (fsm_id=1)...")
        requests.post("http://localhost:8000/api/set_state?state=1")
        
        # Wait for state update
        print("   Waiting for state_changed broadcast...")
        message = await websocket.recv()
        data = json.loads(message)
        
        if data['type'] == 'state_changed':
            print(f"\n5. ✓ Received state_changed broadcast")
            print(f"   fsm_state: {data['fsm_state']}")
            allowed = data.get('allowed_transitions', [])
            print(f"   allowed_transitions: {allowed}")
            
            # Verify DAMP allows START, SQUAT, etc.
            expected = ['ZERO_TORQUE', 'DAMP', 'START', 'SQUAT', 'STAND_UP', 'SIT']
            missing = [s for s in expected if s not in allowed]
            
            if missing:
                print(f"\n   ❌ FAILED: Missing transitions: {missing}")
                print(f"   Expected: {expected}")
                return False
            else:
                print(f"\n   ✅ PASSED: DAMP mode shows correct transitions")
                print(f"   UI buttons for {expected} should be enabled")
                return True
        else:
            print(f"\n   ❌ FAILED: Got {data['type']} instead of state_changed")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_ui_updates())
    if result:
        print("\n" + "=" * 60)
        print("✅ UI UPDATE TEST PASSED")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ UI UPDATE TEST FAILED")
        print("=" * 60)
