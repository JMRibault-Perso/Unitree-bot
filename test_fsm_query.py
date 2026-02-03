#!/usr/bin/env python3
"""
Test script to verify FSM state query API
"""

import asyncio
import sys
import json
import os

# Add the local WebRTC driver to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs', 'go2_webrtc_connect'))

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

ROBOT_IP = "192.168.86.11"
ROBOT_SN = "G1_6002"

async def test_fsm_query():
    """Test querying FSM state from robot"""
    
    print("Connecting to robot...")
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    await conn.connect()
    print("✅ Connected\n")
    
    # Test 1: Query FSM mode (API 7002)
    print("=" * 60)
    print("Test 1: Query FSM Mode (API 7002)")
    print("=" * 60)
    
    response_data = None
    
    def on_response(data: dict):
        nonlocal response_data
        print(f"📥 Received response: {data}")
        if isinstance(data, dict) and data.get('api_id') == 7002:
            response_data = data
    
    # Subscribe to responses
    conn.datachannel.pub_sub.subscribe("rt/api/sport/response", on_response)
    
    # Send query
    payload = {
        "api_id": 7002,  # GET_FSM_MODE
        "parameter": "{}"
    }
    
    print(f"📤 Sending: {payload}")
    await conn.datachannel.pub_sub.publish_request_new("rt/api/sport/request", payload)
    
    # Wait for response
    print("⏳ Waiting for response...")
    for i in range(20):
        if response_data:
            break
        await asyncio.sleep(0.1)
    
    if response_data:
        print(f"\n✅ Got response!")
        print(f"   Full response: {json.dumps(response_data, indent=2)}")
        if 'data' in response_data:
            fsm_mode = response_data['data']
            print(f"   FSM Mode: {fsm_mode}")
    else:
        print("\n❌ No response received")
    
    # Test 2: Subscribe to sportmodestate topic
    print("\n" + "=" * 60)
    print("Test 2: Subscribe to rt/sportmodestate")
    print("=" * 60)
    
    state_updates = []
    
    def on_state(data: dict):
        state_updates.append(data)
        print(f"🤖 State update: {data.get('data', {}).keys() if isinstance(data.get('data'), dict) else data}")
    
    conn.datachannel.pub_sub.subscribe("rt/sportmodestate", on_state)
    print("⏳ Listening for state updates (5 seconds)...")
    
    await asyncio.sleep(5)
    
    if state_updates:
        print(f"\n✅ Received {len(state_updates)} state updates")
        print(f"   Sample: {json.dumps(state_updates[0], indent=2)}")
    else:
        print("\n❌ No state updates received")
    
    print("\n" + "=" * 60)
    print("Disconnecting...")
    await conn.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test_fsm_query())
