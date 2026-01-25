#!/usr/bin/env python3
"""
Final integration test - verify web UI state sync works end-to-end
"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8000"

async def test_web_ui():
    """Test web UI API endpoints"""
    
    print("=" * 80)
    print("WEB UI INTEGRATION TEST")
    print("=" * 80)
    print()
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Connect to robot
        print("1. Testing /api/connect endpoint...")
        async with session.post(f"{API_BASE}/api/connect", json={
            "robot_ip": "192.168.86.2",
            "robot_sn": "E21D1000PAHBMB06"
        }) as resp:
            result = await resp.json()
            if result.get('status') == 'connected':
                print(f"   ✅ Connected: {result.get('message')}")
            else:
                print(f"   ❌ Failed: {result}")
                return
        
        # Wait for state subscription to initialize
        print("   Waiting 2 seconds for state subscription...")
        await asyncio.sleep(2)
        
        # Test 2: Get current state
        print()
        print("2. Testing /api/state endpoint...")
        async with session.get(f"{API_BASE}/api/state") as resp:
            state = await resp.json()
            fsm_id = state.get('fsm_state')
            fsm_name = state.get('fsm_state_name')
            fsm_mode = state.get('fsm_mode')
            allowed = state.get('allowed_transitions', [])
            
            print(f"   Current State:")
            print(f"     FSM ID:    {fsm_id}")
            print(f"     FSM Name:  {fsm_name}")
            print(f"     FSM Mode:  {fsm_mode}")
            print(f"     Allowed Transitions: {len(allowed)} states")
            
            if fsm_id == 801:
                print(f"   ✅ State sync working! Robot in EXPERT_MODE (801)")
            elif fsm_id == 0:
                print(f"   ⚠️  Robot reported as ZERO_TORQUE - may not have synced yet")
            else:
                print(f"   ✅ Robot in valid state {fsm_name}")
        
        # Test 3: Try a state transition (DAMP is always allowed)
        print()
        print("3. Testing state transition (to DAMP mode)...")
        async with session.post(f"{API_BASE}/api/fsm/set_state", json={
            "state": 1  # DAMP
        }) as resp:
            result = await resp.json()
            if result.get('success'):
                print(f"   ✅ Command accepted: {result.get('message')}")
            else:
                print(f"   ❌ Command failed: {result.get('message')}")
        
        # Wait for state to update
        await asyncio.sleep(1)
        
        # Test 4: Verify state changed
        print()
        print("4. Verifying state changed to DAMP...")
        async with session.get(f"{API_BASE}/api/state") as resp:
            state = await resp.json()
            fsm_id = state.get('fsm_state')
            fsm_name = state.get('fsm_state_name')
            
            if fsm_id == 1:
                print(f"   ✅ State changed to DAMP!")
            else:
                print(f"   ⚠️  State is {fsm_name} ({fsm_id}) - may need more time")
        
        # Test 5: Disconnect
        print()
        print("5. Testing /api/disconnect endpoint...")
        async with session.post(f"{API_BASE}/api/disconnect") as resp:
            result = await resp.json()
            if result.get('status') == 'disconnected':
                print(f"   ✅ Disconnected: {result.get('message')}")
            else:
                print(f"   ❌ Failed: {result}")
    
    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print()
    print("You can now access the web UI at: http://localhost:8000")
    print("Try it in your browser to see live state updates!")

if __name__ == "__main__":
    asyncio.run(test_web_ui())
