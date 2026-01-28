#!/usr/bin/env python3
"""
Test the UI: Connect to robot, monitor WebSocket, verify button states
"""
import asyncio
import json
import requests
from websockets import connect

BASE_URL = "http://localhost:8000"

async def test_ui():
    print("=" * 60)
    print("Testing G1 Web UI")
    print("=" * 60)
    
    # Step 1: Discover robot
    print("\n1. Discovering robots...")
    resp = requests.get(f"{BASE_URL}/api/discover")
    data = resp.json()
    if not data["success"] or not data["robots"]:
        print("❌ No robots found!")
        return
    robot = data["robots"][0]
    print(f"✓ Found robot: {robot['serial_number']} at {robot['ip']}")
    
    # Step 2: Connect to robot
    print(f"\n2. Connecting to {robot['ip']}...")
    resp = requests.post(f"{BASE_URL}/api/connect", params={
        "ip": robot["ip"],
        "serial_number": robot["serial_number"]
    })
    data = resp.json()
    if not data["success"]:
        print(f"❌ Connect failed: {data.get('error')}")
        return
    print("✓ Connected to robot")
    
    # Step 3: Wait for robot to stabilize
    await asyncio.sleep(2)
    
    # Step 4: Get current state
    print("\n3. Getting current state...")
    resp = requests.get(f"{BASE_URL}/api/state")
    data = resp.json()
    if data["success"]:
        state = data["state"]
        print(f"✓ Current state: {state['fsm_state']} (value={state['fsm_state_value']})")
        print(f"✓ Allowed transitions: {state['allowed_transitions']}")
        
        # Verify allowed transitions match state
        fsm_state = state['fsm_state']
        allowed = state['allowed_transitions']
        
        if fsm_state == "ZERO_TORQUE":
            if "DAMP" in allowed and "START" not in allowed:
                print("✅ ZERO_TORQUE transitions CORRECT (DAMP allowed, START not allowed)")
            else:
                print(f"❌ ZERO_TORQUE transitions WRONG: {allowed}")
        elif fsm_state == "DAMP":
            if "START" in allowed and "SQUAT" in allowed:
                print("✅ DAMP transitions CORRECT (START and SQUAT allowed)")
            else:
                print(f"❌ DAMP transitions WRONG: {allowed}")
        else:
            print(f"ℹ️  State {fsm_state} transitions: {allowed}")
    
    # Step 5: Monitor WebSocket for real-time updates
    print("\n4. Monitoring WebSocket for state changes...")
    print("   (Waiting 10 seconds - change robot state using R3-1 or app)")
    
    try:
        async with connect(f"ws://localhost:8000/ws") as websocket:
            # Listen for 10 seconds
            end_time = asyncio.get_event_loop().time() + 10
            while asyncio.get_event_loop().time() < end_time:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(msg)
                    
                    if data.get("type") == "state_changed":
                        state = data.get("state", {})
                        fsm_state = state.get("fsm_state")
                        allowed = state.get("allowed_transitions", [])
                        
                        print(f"\n   📡 State change: {fsm_state}")
                        print(f"   📋 Allowed: {allowed}")
                        
                        # Verify
                        if fsm_state == "DAMP":
                            if "START" in allowed and "SQUAT" in allowed:
                                print("   ✅ DAMP transitions CORRECT!")
                            else:
                                print(f"   ❌ DAMP transitions WRONG!")
                except asyncio.TimeoutError:
                    continue
    except Exception as e:
        print(f"⚠️  WebSocket error: {e}")
    
    # Step 6: Disconnect
    print("\n5. Disconnecting...")
    resp = requests.post(f"{BASE_URL}/api/disconnect")
    print("✓ Disconnected")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_ui())
