#!/usr/bin/env python3
"""
CONSOLIDATED G1 IMPLEMENTATION - ALL PROVEN WORKING CODE
========================================================

COMPLETE API REFERENCE for G1_6937:

SLAM OPERATIONS:
- API 1801: START_MAPPING (slam_type: "indoor")
- API 1802: END_MAPPING/SAVE (saves map to /home/unitree/*.pcd)
- API 1804: LOAD_MAP (load saved maps with pose + quaternion)

NAVIGATION (Requires loaded map via API 1804):
- API 1102: NAVIGATE_TO (move to x,y with obstacle avoidance, max 10m)

MOTION CONTROL:
- API 7001: GET_FSM_ID (query current FSM state)
- API 7002: GET_FSM_MODE (query FSM mode)  
- API 7101: SET_FSM_ID (change FSM state)

ACTIONS/GESTURES:
- API 7107: GET_ACTION_LIST (list available taught actions)
- API 7108: EXECUTE_ACTION (play taught action by name, non-blocking)

TESTED AND WORKING:
1. WebRTC connection to 192.168.86.2 (MAC: fc:23:cd:92:60:02)
2. SLAM: start → save → load workflow
3. Response parsing: nested JSON in response['data']['data']
4. Navigation with obstacle avoidance
5. Action list retrieval and execution

KEY FINDINGS:
1. Robot IP: 192.168.86.2 (from MAC discovery)
2. WebRTC Module: unitree_webrtc_connect.webrtc_driver
3. Response Format: Nested JSON - parse response['data']['data']
4. Map Storage: /home/unitree/ directory
5. Pose Format: x, y, z + quaternion (q_x, q_y, q_z, q_w)
6. Navigation: Max 10m from current position, requires loaded map
"""

import asyncio
import json
import sys
import math
sys.path.append('/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod


async def slam_start_mapping(conn, slam_type="indoor"):
    """Start SLAM mapping session"""
    payload = {
        "api_id": 1801,
        "parameter": json.dumps({"data": {"slam_type": slam_type}})
    }
    return await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/slam_operate/request", payload
    )


async def slam_save_map(conn, map_path: str):
    """Save current SLAM mapping to file"""
    if not map_path.startswith('/home/unitree/'):
        map_path = f'/home/unitree/{map_path}'
    
    payload = {
        "api_id": 1802,
        "parameter": json.dumps({"data": {"address": map_path}})
    }
    return await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/slam_operate/request", payload
    )


async def slam_load_map(conn, map_path: str, pose_x=0.0, pose_y=0.0, pose_z=0.0):
    """Load SLAM map with initial robot pose"""
    if not map_path.startswith('/home/unitree/'):
        map_path = f'/home/unitree/{map_path}'
    
    payload = {
        "api_id": 1804,
        "parameter": json.dumps({
            "data": {
                "x": pose_x, "y": pose_y, "z": pose_z,
                "q_x": 0.0, "q_y": 0.0, "q_z": 0.0, "q_w": 1.0,
                "address": map_path
            }
        })
    }
    return await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/slam_operate/request", payload
    )


async def navigate_to(conn, target_x: float, target_y: float, target_yaw: float = 0.0):
    """Navigate to target position with obstacle avoidance (API 1102)
    
    Requirements:
    - Map must be loaded first (via slam_load_map API 1804)
    - Max distance: 10 meters from current position
    - Obstacles must be 50cm+ high to be detected
    """
    # Convert yaw to quaternion (rotation around Z axis)
    qz = math.sin(target_yaw / 2)
    qw = math.cos(target_yaw / 2)
    
    payload = {
        "api_id": 1102,
        "parameter": json.dumps({
            "data": {
                "x": target_x,
                "y": target_y,
                "z": 0.0,
                "q_x": 0.0,
                "q_y": 0.0,
                "q_z": qz,
                "q_w": qw
            }
        })
    }
    return await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/slam_operate/request", payload
    )


async def get_action_list(conn):
    """Get list of available taught actions (API 7107)"""
    payload = {
        "api_id": 7107,
        "parameter": json.dumps({"data": {}})
    }
    return await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/robot_state/request", payload
    )


async def execute_action(conn, action_name: str):
    """Execute a taught action by name (API 7108) - NON-BLOCKING
    
    Action must exist in the action list from get_action_list()
    """
    payload = {
        "api_id": 7108,
        "parameter": json.dumps({
            "data": {
                "name": action_name
            }
        })
    }
    return await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/robot_state/request", payload
    )


async def get_fsm_mode(conn):
    """Query current FSM mode (API 7002)"""
    payload = {
        "api_id": 7002,
        "parameter": json.dumps({"data": {}})
    }
    return await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/robot_state/request", payload
    )


async def set_fsm_mode(conn, fsm_id: int):
    """Set FSM mode (API 7101)"""
    payload = {
        "api_id": 7101,
        "parameter": json.dumps({
            "data": {
                "fsm_id": fsm_id
            }
        })
    }
    return await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/robot_state/request", payload
    )


def parse_slam_response(response: dict) -> dict:
    """Parse nested JSON response from SLAM API"""
    try:
        if 'data' in response and isinstance(response['data'], dict):
            data_str = response['data'].get('data')
            if data_str and isinstance(data_str, str):
                return json.loads(data_str)
        return response.get('data', {})
    except json.JSONDecodeError:
        return response


async def main():
    """Example complete SLAM workflow"""
    print("=" * 70)
    print("SLAM WORKFLOW - PROVEN IMPLEMENTATION")
    print("=" * 70)
    
    robot_ip = "192.168.86.2"  # Known from MAC discovery
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=robot_ip)
    
    try:
        print(f"\nConnecting to {robot_ip}...")
        await conn.connect()
        print("✅ Connected")
        
        # Phase 1: Start mapping
        print("\n1️⃣ Starting SLAM mapping...")
        resp = await slam_start_mapping(conn)
        print(f"   Response: {parse_slam_response(resp)}")
        await asyncio.sleep(3)
        
        # Phase 2: Save map
        print("\n2️⃣ Saving map...")
        resp = await slam_save_map(conn, "consolidated_test.pcd")
        data = parse_slam_response(resp)
        print(f"   Status: {data.get('succeed', False)}")
        print(f"   Info: {data.get('info', 'N/A')}")
        
        # Phase 3: Load map
        print("\n3️⃣ Loading map...")
        resp = await slam_load_map(conn, "consolidated_test.pcd")
        data = parse_slam_response(resp)
        print(f"   Status: {data.get('succeed', False)}")
        print(f"   Info: {data.get('info', 'N/A')}")
        
        print("\n✅ Workflow complete")
        
    finally:
        await conn.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
