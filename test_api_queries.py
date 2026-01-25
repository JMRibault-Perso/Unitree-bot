#!/usr/bin/env python3
"""
Test script to verify which API returns the correct FSM state
Tests both API 7001 (GET_FSM_ID) and API 7002 (GET_FSM_MODE)
"""

import asyncio
import sys
import json

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

ROBOT_IP = "192.168.86.2"
ROBOT_SN = "E21D1000PAHBMB06"

async def test_api_queries():
    """Test all FSM query APIs"""
    
    print("=" * 70)
    print("FSM State Query API Test")
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
    
    # Store all responses
    all_responses = []
    
    def on_response(data: dict):
        all_responses.append(data)
        print(f"📥 Response: {json.dumps(data, indent=2)}\n")
    
    # Subscribe to responses
    conn.datachannel.pub_sub.subscribe("rt/api/sport/response", on_response)
    
    # Wait a bit for subscription to register
    await asyncio.sleep(0.5)
    
    # Test 1: API 7001 - GET_FSM_ID
    print("=" * 70)
    print("Test 1: API 7001 (GET_FSM_ID)")
    print("=" * 70)
    payload_7001 = {
        "api_id": 7001,
        "parameter": "{}"
    }
    print(f"📤 Sending: {payload_7001}")
    await conn.datachannel.pub_sub.publish_request_new("rt/api/sport/request", payload_7001)
    await asyncio.sleep(0.5)
    
    # Test 2: API 7002 - GET_FSM_MODE
    print("=" * 70)
    print("Test 2: API 7002 (GET_FSM_MODE)")
    print("=" * 70)
    payload_7002 = {
        "api_id": 7002,
        "parameter": "{}"
    }
    print(f"📤 Sending: {payload_7002}")
    await conn.datachannel.pub_sub.publish_request_new("rt/api/sport/request", payload_7002)
    await asyncio.sleep(0.5)
    
    # Parse results
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    for resp in all_responses:
        if resp.get('type') == 'res':
            inner_data = resp.get('data', {})
            header = inner_data.get('header', {})
            identity = header.get('identity', {})
            api_id = identity.get('api_id')
            
            data_str = inner_data.get('data', '{}')
            try:
                parsed_data = json.loads(data_str) if isinstance(data_str, str) else data_str
            except:
                parsed_data = data_str
            
            api_name = {7001: 'GET_FSM_ID', 7002: 'GET_FSM_MODE'}.get(api_id, f'API {api_id}')
            
            print(f"\n{api_name} (API {api_id}):")
            print(f"  Raw data: {data_str}")
            print(f"  Parsed: {parsed_data}")
            
            if isinstance(parsed_data, dict) and 'data' in parsed_data:
                value = parsed_data['data']
                print(f"  Value: {value}")
                
                # Map to FSM state names
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
                
                state_name = fsm_map.get(value, f"Unknown state {value}")
                print(f"  → FSM State: {state_name}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION:")
    print("=" * 70)
    print("The API that returns 500 (LOCK_STAND) when robot is in walk/run mode")
    print("is the CORRECT one to use for initial state detection.")
    print("=" * 70)
    
    print("\nDisconnecting...")
    await conn.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(test_api_queries())
